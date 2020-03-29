from contextlib import contextmanager as contextmanager
import os
import tempfile

from .fs import remove_tree
from .log import debug


__all__ = ['TemporaryDirectory']


@contextmanager
def TemporaryDirectory():
    '''Create a temporary directory (Python 2 wrapper)
    '''
    tmpdir = tempfile.mkdtemp(prefix='python-appimage-')
    debug('MKDIR', tmpdir)
    pwd = os.getcwd()
    os.chdir(tmpdir)
    try:
        yield tmpdir
    finally:
        os.chdir(pwd)
        remove_tree(tmpdir)
