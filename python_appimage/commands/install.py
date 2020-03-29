import os

from ..utils import deps
from ..utils.log import log


__all__ = ['execute']


def _unpack_args(args):
    '''Unpack command line arguments
    '''
    return args.binary


def execute(*args):
    '''Install the requested dependencies
    '''
    bindir = os.path.dirname(deps.PATCHELF)
    for binary in args:
        installed = getattr(deps, 'ensure_' + binary)()
        words = 'has been' if installed else 'already' 
        log('INSTALL',
            '{:} {:} installed in {:}'.format(binary, words, bindir))
