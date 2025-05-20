import glob
import os
from pathlib import Path
import platform
import shutil
import sys

from ...appimage import build_appimage, relocate_python
from ...manylinux import Arch, Downloader, ImageExtractor, LinuxTag, \
                         PythonExtractor
from ...utils.docker import docker_run
from ...utils.fs import copy_tree
from ...utils.manylinux import format_appimage_name, format_tag
from ...utils.tmp import TemporaryDirectory


__all__ = ['execute']


def _unpack_args(args):
    '''Unpack command line arguments
    '''
    return args.tag, args.abi


def _get_appimage_name(abi, tag):
    '''Format the Python AppImage name using the ABI and OS tags
    '''
    # Read the Python version from the desktop file
    desktop = glob.glob('AppDir/python*.desktop')[0]
    fullversion = desktop[13:-8]

    # Finish building the AppImage on the host. See below.
    return format_appimage_name(abi, fullversion, tag)


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
