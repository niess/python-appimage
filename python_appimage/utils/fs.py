from distutils.dir_util import mkpath as _mkpath, remove_tree as _remove_tree
from distutils.file_util import copy_file as _copy_file
import errno
import os

from .log import debug


__all__ = ['copy_file', 'copy_tree', 'make_tree', 'remove_file', 'remove_tree']


# Wrap some file system related functions
def make_tree(path):
    '''Create directories recursively if they don't exist
    '''
    debug('MKDIR', path)
    return _mkpath(path)


def copy_file(source, destination, update=False, verbose=True):
    '''
    '''
    name = os.path.basename(source)
    if verbose:
        debug('COPY', '%s from %s', name, os.path.dirname(source))
    _copy_file(source, destination, update=update)


def copy_tree(source, destination):
    '''Copy (or update) a directory preserving symlinks
    '''
    if not os.path.exists(source):
        raise OSError(errno.ENOENT, 'No such file or directory: ' + source)

    name = os.path.basename(source)
    debug('COPY', '%s from %s', name, os.path.dirname(source))

    for root, _, files in os.walk(source):
        relpath = os.path.relpath(root, source)
        dirname = os.path.join(destination, relpath)
        _mkpath(dirname)
        for file_ in files:
            src = os.path.join(root, file_)
            dst = os.path.join(dirname, file_)
            if os.path.islink(src):
                try:
                    os.remove(dst)
                except OSError:
                    pass
                linkto = os.readlink(src)
                os.symlink(linkto, dst)
            else:
                copy_file(src, dst, update=True, verbose=False)


def remove_file(path):
    '''remove a file if it exists
    '''
    name = os.path.basename(path)
    debug('REMOVE', '%s from %s', name, os.path.dirname(path))
    try:
        os.remove(path)
    except OSError:
        pass


def remove_tree(path):
    '''remove a directory if it exists
    '''
    name = os.path.basename(path)
    debug('REMOVE', '%s from %s', name, os.path.dirname(path))
    try:
        _remove_tree(path)
    except OSError:
        pass
