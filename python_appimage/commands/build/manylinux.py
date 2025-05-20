import os
from pathlib import Path
import shutil

from ...appimage import build_appimage
from ...manylinux import Arch, Downloader, ImageExtractor, LinuxTag, \
                         PythonExtractor
from ...utils.tmp import TemporaryDirectory


__all__ = ['execute']


def _unpack_args(args):
    '''Unpack command line arguments
    '''
    return args.tag, args.abi


def execute(tag, abi):
    '''Build a Python AppImage using a Manylinux image
    '''

    tag, arch = tag.split('_', 1)
    tag = LinuxTag.from_brief(tag)
    arch = Arch.from_str(arch)

    downloader = Downloader(tag=tag, arch=arch)
    downloader.download()

    image_extractor = ImageExtractor(downloader.default_destination())
    image_extractor.extract()

    pwd = os.getcwd()
    with TemporaryDirectory() as tmpdir:
        python_extractor = PythonExtractor(
            arch = arch,
            prefix = image_extractor.default_destination(),
            tag = abi
        )
        appdir = Path(tmpdir) / 'AppDir'
        python_extractor.extract(appdir, appify=True)

        fullname = '-'.join((
            f'{python_extractor.impl}{python_extractor.version.long()}',
            abi,
            f'{tag}_{arch}'
        ))

        destination = f'{fullname}.AppImage'
        build_appimage(
            appdir = str(appdir),
            destination = destination
        )
        shutil.move(
            Path(tmpdir) / destination,
            Path(pwd) / destination
        )
