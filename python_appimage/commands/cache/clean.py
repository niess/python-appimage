import glob
import json
import os
from pathlib import Path
import subprocess

from ...utils.deps import CACHE_DIR
from ...utils.fs import remove_file, remove_tree
from ...utils.log import log


__all__ = ['execute']


def _unpack_args(args):
    '''Unpack command line arguments
    '''
    return (args.tags, args.all)


def execute(images, all_):
    '''Clean cached image(s)
    '''

    cache = Path(CACHE_DIR)

    if not images:
        images = [image[9:] for image in sorted(os.listdir(cache /
                                                         'share/images'))]

    for image in images:
        try:
            image, tag = image.rsplit(':', 1)
        except ValueError:
            tag = None

        if not image.replace('_', '').isalnum():
            raise ValueError(f'bad image tag ({image})')

        path = cache / f'share/images/manylinux{image}'
        if not path.exists():
            raise ValueError(f'no such image ({image})')

        if tag is None:
            if not all_:
                path = path / 'extracted'
            remove_tree(str(path))
        else:
            tag_file = path / f'tags/{tag}.json'
            if not tag_file.exists():
                raise ValueError(f'no such image ({image}:{tag})')

            if all_:
                with tag_file.open() as f:
                    layers = json.load(f)["layers"]
                for layer in layers:
                    layer = path / f'layers/{layer}.tar.gz'
                    if layer.exists():
                        remove_file(str(layer))
                remove_file(str(tag_file))
            else:
                path = cache / f'share/images/{image}/extracted/{tag}'
                if path.exists():
                    remove_tree(str(path))
