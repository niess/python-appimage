import glob
from pathlib import Path

from ..manylinux import ensure_image, PythonVersion
from ..utils.log import log


__all__ = ['execute']


def _unpack_args(args):
    '''Unpack command line arguments
    '''
    return (args.tag,)


def execute(tag):
    '''List python versions installed in a manylinux image
    '''

    image = ensure_image(tag)

    pythons = []
    for path in glob.glob(str(image.path / 'opt/python/cp*')):
        path = Path(path)
        version = PythonVersion.from_str(path.readlink().name[8:]).long()
        pythons.append((path.name, version))
    pythons = sorted(pythons)

    for (abi, version) in pythons:
        log('LIST', "{:8} ->  /opt/python/{:}".format(version, abi))

    return pythons
