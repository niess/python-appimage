from types import SimpleNamespace

from .config import Arch, LinuxTag, PythonImpl, PythonVersion
from .download import Downloader
from .extract import ImageExtractor, PythonExtractor
from .patch import Patcher


__all__ = ['Arch', 'Downloader', 'ensure_image', 'ImageExtractor', 'LinuxTag',
           'Patcher', 'PythonExtractor', 'PythonImpl', 'PythonVersion']


def ensure_image(tag, *, clean=False, extract=True):
    '''Download a manylinux image to the cache'''

    try:
        tag, image_tag = tag.rsplit(':', 1)
    except ValueError:
        image_tag = 'latest'

    if tag.startswith('2_'):
        tag, arch = tag[2:].split('_', 1)
        tag = f'2_{tag}'
    else:
        tag, arch = tag.split('_', 1)
    tag = LinuxTag.from_brief(tag)
    arch = Arch.from_str(arch)

    downloader = Downloader(tag=tag, arch=arch)
    downloader.download(tag=image_tag)

    if extract:
        image_extractor = ImageExtractor(
            prefix = downloader.default_destination(),
            tag = image_tag
        )
        image_extractor.extract(clean=clean)

        patcher = Patcher(tag=tag, arch=arch)
        patcher.patch(destination = image_extractor.default_destination())

        return SimpleNamespace(
            arch = arch,
            tag = tag,
            path = image_extractor.default_destination(),
        )
    else:
        return SimpleNamespace(
            arch = arch,
            tag = tag,
            path = downloader.default_destination(),
        )
