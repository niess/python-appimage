from types import SimpleNamespace

from .config import Arch, LinuxTag, PythonImpl, PythonVersion
from .download import Downloader
from .extract import ImageExtractor, PythonExtractor


__all__ = ['Arch', 'Downloader', 'ensure_image', 'ImageExtractor', 'LinuxTag',
           'PythonExtractor', 'PythonImpl', 'PythonVersion']


def ensure_image(tag):
    '''Extract a manylinux image to the cache'''

    tag, arch = tag.split('_', 1)
    tag = LinuxTag.from_brief(tag)
    arch = Arch.from_str(arch)

    downloader = Downloader(tag=tag, arch=arch)
    downloader.download()

    image_extractor = ImageExtractor(downloader.default_destination())
    image_extractor.extract()

    return SimpleNamespace(
        arch = arch,
        tag = tag,
        path = image_extractor.default_destination(),
    )
