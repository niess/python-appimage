import os
from pathlib import Path
import shutil

from ...appimage import build_appimage
from ...manylinux import ensure_image, PythonExtractor
from ...utils.tmp import TemporaryDirectory


__all__ = ['execute']


def _unpack_args(args):
    '''Unpack command line arguments
    '''
    return args.tag, args.abi, args.clean


def execute(tag, abi, clean):
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
        python_extractor.extract(appdir, appify=True)

        fullname = '-'.join((
            f'{python_extractor.impl}{python_extractor.version.long()}',
            abi,
            f'{image.tag}_{image.arch}'
        ))

        destination = f'{fullname}.AppImage'
        build_appimage(
            appdir = str(appdir),
            destination = destination
        )
        shutil.copy(
            Path(tmpdir) / destination,
            Path(pwd) / destination
        )
