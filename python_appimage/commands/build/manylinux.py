import os
from pathlib import Path
import tarfile

from ...appimage import build_appimage
from ...manylinux import ensure_image, PythonExtractor
from ...utils.fs import copy_file, copy_tree
from ...utils.log import log
from ...utils.tmp import TemporaryDirectory


__all__ = ['execute']


def _unpack_args(args):
    '''Unpack command line arguments
    '''
    return args.tag, args.abi, args.bare, args.clean, args.no_packaging


def execute(tag, abi, bare=False, clean=False, no_packaging=False):
    '''Build a Python AppImage using a Manylinux image
    '''

    image = ensure_image(tag, clean=clean)

    pwd = os.getcwd()
    with TemporaryDirectory() as tmpdir:
        python_extractor = PythonExtractor(
            arch = image.arch,
            prefix = image.path,
            tag = abi
        )
        appdir = Path(tmpdir) / 'AppDir'
        appify = not bare
        python_extractor.extract(appdir, appify=appify)

        fullname = '-'.join((
            f'{python_extractor.impl}{python_extractor.version.long()}',
            abi,
            f'{image.tag}_{image.arch}'
        ))

        if no_packaging:
            copy_tree(
                Path(tmpdir) / 'AppDir',
                Path(pwd) / fullname
            )
        elif bare:
            log('COMPRESS', fullname)
            destination = f'{fullname}.tar.gz'
            tar_path = Path(tmpdir) / destination
            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(appdir, arcname=fullname)
            copy_file(
                tar_path,
                Path(pwd) / destination
            )
        else:
            destination = f'{fullname}.AppImage'
            build_appimage(
                appdir = str(appdir),
                arch = str(image.arch),
                destination = destination
            )
            copy_file(
                Path(tmpdir) / destination,
                Path(pwd) / destination
            )
