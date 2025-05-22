from dataclasses import dataclass, field
import glob
import hashlib
import json
from pathlib import Path
import requests
import shutil
import tempfile
from typing import Optional

from .config import Arch, LinuxTag
from ..utils.deps import CACHE_DIR
from ..utils.log import debug, log


CHUNK_SIZE = 8189

SUCCESS = 200


class DownloadError(Exception):
    pass


@dataclass(frozen=True)
class Downloader:

    '''Manylinux tag.'''
    tag: LinuxTag

    '''Platform architecture.'''
    arch: Optional[Arch] = None

    '''Docker image.'''
    image: str = field(init=False)

    '''Authentication token.'''
    token: str = field(init=False)


    def __post_init__(self):
        # Set host arch if not explictly specified.
        if self.arch is None:
            arch = Arch.from_host()
            object.__setattr__(self, 'arch', arch)

        # Set image name.
        image = f'{self.tag}_{self.arch}'
        object.__setattr__(self, 'image', image)


    def default_destination(self):
        return Path(CACHE_DIR) / f'share/images/{self.image}'


    def download(
        self,
        destination: Optional[Path]=None,
        *,
        tag: Optional[str] = 'latest'
        ):
        '''Download Manylinux image'''

        destination = destination or self.default_destination()

        # Authenticate to quay.io.
        repository = f'pypa/{self.image}'
        log('PULL', f'{self.image}:{tag}')
        url = 'https://quay.io/v2/auth'
        url = f'{url}?service=quay.io&scope=repository:{repository}:pull'
        debug('GET', url)
        r = requests.request('GET', url)
        if r.status_code == SUCCESS:
            object.__setattr__(self, 'token', r.json()['token'])
        else:
            raise DownloadError(r.status_code, r.text, r.headers)

        # Fetch image manifest.
        repository = f'pypa/{self.image}'
        url = f'https://quay.io/v2/{repository}/manifests/{tag}'
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/vnd.docker.distribution.manifest.v2+json'
        }
        debug('GET', url)
        r = requests.request('GET', url, headers=headers)
        if r.status_code == SUCCESS:
            image_digest = r.headers['Docker-Content-Digest'].split(':', 1)[-1]
            manifest = r.json()
        else:
            raise DownloadError(r.status_code, r.text, r.headers)

        # Check missing layers to download.
        required = [layer['digest'].split(':', 1)[-1] for layer in
                    manifest['layers']]

        missing = []
        for hash_ in required:
            path = destination / f'layers/{hash_}.tar.gz'
            if path.exists():
                hasher = hashlib.sha256()
                with path.open('rb') as f:
                    while True:
                        chunk = f.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        else:
                            hasher.update(chunk)
                    h = hasher.hexdigest()
                    if h != hash_:
                        missing.append(hash_)
                    else:
                        debug('FOUND', f'{hash_}.tar.gz')
            else:
                missing.append(hash_)

        # Fetch missing layers.
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            for i, hash_ in enumerate(missing):
                debug('DOWNLOAD', f'{self.image}:{tag} '
                                  f'[{i + 1} / {len(missing)}]')

                filename = f'{hash_}.tar.gz'
                url = f'https://quay.io/v2/{repository}/blobs/sha256:{hash_}'
                debug('GET', url)
                r = requests.request('GET', url, headers=headers, stream=True)
                if r.status_code == SUCCESS:
                    debug('STREAM', filename)
                else:
                    raise DownloadError(r.status_code, r.text, r.headers)

                hasher = hashlib.sha256()
                tmp = workdir / 'layer.tgz'
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)
                            hasher.update(chunk)

                    h = hasher.hexdigest()
                    if h != hash_:
                        raise DownloadError(
                            f'bad hash (expected {hash_}, found {h})'
                        )
                layers_dir = destination / 'layers'
                layers_dir.mkdir(exist_ok=True, parents=True)
                shutil.move(tmp, layers_dir / filename)

        tags_dir = destination / 'tags'
        tags_dir.mkdir(exist_ok=True, parents=True)
        with open(tags_dir / f'{tag}.json', "w") as f:
            json.dump({'digest': image_digest, 'layers': required}, f)

        # Remove unused layers.
        required = set(required)
        for tag in glob.glob(str(destination / 'tags/*.json')):
            with open(tag) as f:
                tag = json.load(f)
                required |= set(tag["layers"])
        required = [f'{hash_}.tar.gz' for hash_ in required]

        for layer in glob.glob(str(destination / 'layers/*.tar.gz')):
            layer = Path(layer)
            if layer.name not in required:
                debug('REMOVE', f'{self.image} [layer/{layer.stem}]')
                layer.unlink()
