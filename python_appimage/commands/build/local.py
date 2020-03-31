import glob
import os
import shutil

from ...appimage import build_appimage, relocate_python
from ...utils.tmp import TemporaryDirectory


__all__ = ['execute']


def _unpack_args(args):
    '''Unpack command line arguments
    '''
    return args.python, args.destination


def execute(python=None, destination=None):
    '''Build a Python AppImage using a local installation
    '''
    pwd = os.getcwd()
    with TemporaryDirectory() as tmpdir:
        relocate_python(python)

        dirname, pattern = None, None
        if destination is not None:
            dirname, destination = os.path.split(destination)
            pattern = destination
        if pattern is None:
            pattern = 'python*.AppImage'
        build_appimage(destination=destination)
        appimage = glob.glob(pattern)[0]
        if dirname is None:
            dirname = pwd
        else:
            os.chdir(pwd)
            dirname = os.path.abspath(dirname)
            os.chdir(tmpdir)
        shutil.move(appimage, os.path.join(dirname, appimage))
