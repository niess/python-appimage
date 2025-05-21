import glob
import os
from pathlib import Path
import subprocess

from ...utils.deps import CACHE_DIR
from ...utils.log import log


__all__ = ['execute']


def _unpack_args(args):
    '''Unpack command line arguments
    '''
    return tuple()


def execute():
    '''List cached image(s)
    '''

    cache = Path(CACHE_DIR)

    images = sorted(os.listdir(cache / 'share/images'))
    for image in images:
        tags = ', '.join((
            tag[:-5] for tag in \
                sorted(os.listdir(cache / f'share/images/{image}/tags'))
        ))
        if not tags:
            continue
        path = cache / f'share/images/{image}'
        memory = _getsize(path)
        log('LIST', f'{image} ({tags}) [{memory}]')


def _getsize(path: Path):
    r = subprocess.run(f'du -sh {path}', capture_output=True, check=True,
                       shell=True)
    return r.stdout.decode().split(None, 1)[0]
