import os

from ..utils import deps
from ..utils.log import log


__all__ = ['execute']


def _unpack_args(args):
    '''Unpack command line arguments
    '''
    return (args.binary,)


def execute(binary):
    '''Print the location of a binary dependency
    '''
    path = os.path.join(os.path.dirname(deps.PATCHELF), binary)
    if os.path.exists(path):
        print(path)
