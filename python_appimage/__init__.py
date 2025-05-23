import platform

from .version import version as __version__


if platform.system() != 'Linux':
    raise RuntimeError('invalid system: ' + platform.system())
