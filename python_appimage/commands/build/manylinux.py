import os
from pathlib import Path
import tarfile
import shutil

from ...appimage import build_appimage
from ...manylinux import ensure_image, PythonExtractor
from ...utils.log import log
from ...utils.tmp import TemporaryDirectory


__all__ = ['execute']


def _unpack_args(args):
    '''Unpack command line arguments
    '''
    return args.tag, args.abi, args.clean, args.tarball


def execute(tag, abi, clean, tarball):
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
        appify = not tarball
        python_extractor.extract(appdir, appify=appify)

        fullname = '-'.join((
            f'{python_extractor.impl}{python_extractor.version.long()}',
            abi,
            f'{image.tag}_{image.arch}'
        ))

        if tarball:
            log('COMPRESS', fullname)
            destination = f'{fullname}.tgz'
            tar_path = Path(tmpdir) / destination
            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(appdir, arcname=fullname)
            shutil.copy(
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
            shutil.copy(
                Path(tmpdir) / destination,
                Path(pwd) / destination
            )
