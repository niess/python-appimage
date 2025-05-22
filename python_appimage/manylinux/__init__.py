from types import SimpleNamespace

from .config import Arch, LinuxTag, PythonImpl, PythonVersion
from .download import Downloader
from .extract import ImageExtractor, PythonExtractor


__all__ = ['Arch', 'Downloader', 'ensure_image', 'ImageExtractor', 'LinuxTag',
           'PythonExtractor', 'PythonImpl', 'PythonVersion']


def ensure_image(tag):
    '''Extract a manylinux image to the cache'''

    try:
        tag, image_tag = tag.rsplit(':', 1)
    except ValueError:
        image_tag = 'latest'

    tag, arch = tag.split('_', 1)
    tag = LinuxTag.from_brief(tag)
    arch = Arch.from_str(arch)

    downloader = Downloader(tag=tag, arch=arch)
    downloader.download(tag=image_tag)

    image_extractor = ImageExtractor(
        prefix = downloader.default_destination(),
        tag = image_tag
    )
    image_extractor.extract()

    return SimpleNamespace(
        arch = arch,
        tag = tag,
        path = image_extractor.default_destination(),
    )
