from dataclasses import dataclass
from pathlib import Path
import os
import stat
import subprocess
from typing import Optional

from .config import Arch, LinuxTag
from ..utils.deps import CACHE_DIR
from ..utils.log import debug, log
from ..utils.url import urlretrieve


@dataclass(frozen=True)
class Patcher:
    '''Manylinux tag.'''
    tag: LinuxTag

    '''Platform architecture.'''
    arch: Optional[Arch] = None


    def patch(self, destination: Path):
        '''Apply any patch'''

        cache = Path(CACHE_DIR) / f'share/patches/'

        if self.tag == LinuxTag.MANYLINUX_1:
            patch = f'tk-manylinux1_{self.arch}'
            log('PATCH', patch)
            tarfile = f'{patch}.tar.gz'
            path = cache / tarfile
            if not path.exists():
                url = f'https://github.com/niess/python-appimage/releases/download/manylinux1/{tarfile}'
                urlretrieve(url, path)
                mode = os.stat(path)[stat.ST_MODE]
                os.chmod(path, mode | stat.S_IWGRP | stat.S_IWOTH)

            debug('EXTRACT', tarfile)
            cmd = ''.join((
                 f'trap \'chmod u+rw -R {destination}\' EXIT ; ',
                 f'mkdir -p {destination} && ',
                 f'tar -xzf {path} -C {destination}',
            ))
            r = subprocess.run(f'/bin/bash -c "{cmd}"', shell=True,
                               capture_output=True)
            if r.returncode != 0:
                raise ValueError(r.stderr.decode())
