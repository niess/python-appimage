import glob
import os
import re
import shutil
import sys

from .appify import Appifier
from ..manylinux import PythonVersion
from ..utils.deps import EXCLUDELIST, PATCHELF, ensure_excludelist, \
                         ensure_patchelf
from ..utils.fs import copy_file, copy_tree, make_tree, remove_file, \
                       remove_tree
from ..utils.log import log
from ..utils.system import ldd, system


__all__ = ['patch_binary', 'relocate_python']


_excluded_libs = None
'''Appimage excluded libraries, i.e. assumed to be installed on the host
'''


def patch_binary(path, libdir, recursive=True):
    '''Patch the RPATH of a binary and fetch its dependencies
    '''
    global _excluded_libs

    if _excluded_libs is None:
        ensure_excludelist()
        excluded = []
        with open(EXCLUDELIST) as f:
            for line in f:
                line = line.strip()
                if (not line) or line.startswith('#'):
                    continue
                excluded.append(line.split(' ', 1)[0])
        _excluded_libs = excluded
    else:
        excluded = _excluded_libs

    deps = ldd(path) # Fetch deps before patching RPATH.

    ensure_patchelf()
    rpath = '\'' + system((PATCHELF, '--print-rpath', path)) + '\''
    relpath = os.path.relpath(libdir, os.path.dirname(path))
    relpath = '' if relpath == '.' else '/' + relpath
    expected = '\'$ORIGIN' + relpath + ':$ORIGIN/../lib\''
    if rpath != expected:
        system((PATCHELF, '--set-rpath', expected, path))

    for dep in deps:
        name = os.path.basename(dep)
        if name in excluded:
            continue
        target = libdir + '/' + name
        if not os.path.exists(target):
            copy_file(dep, target)
            if recursive:
                patch_binary(target, libdir, recursive=True)


def relocate_python(python=None, appdir=None):
    '''Bundle a Python install inside an AppDir
    '''

    if python is not None:
        if not os.path.exists(python):
            raise ValueError('could not access ' + python)

    if appdir is None:
        appdir = 'AppDir'


    # Set some key variables & paths
    if python:
        FULLVERSION = system((python, '-c', '"import sys; print(sys.version)"'))
        FULLVERSION = FULLVERSION.strip()
    else:
        FULLVERSION = sys.version
    FULLVERSION = FULLVERSION.split(None, 1)[0]
    VERSION = '.'.join(FULLVERSION.split('.')[:2])
    PYTHON_X_Y = 'python' + VERSION
    PIP_X_Y = 'pip' + VERSION
    PIP_X = 'pip' + VERSION[0]

    APPDIR = os.path.abspath(appdir)
    APPDIR_BIN = APPDIR + '/usr/bin'
    APPDIR_LIB = APPDIR + '/usr/lib'
    APPDIR_SHARE = APPDIR + '/usr/share'

    if python:
        HOST_PREFIX = system((
            python, '-c', '"import sys; print(sys.prefix)"')).strip()
    else:
        HOST_PREFIX = sys.prefix
    HOST_BIN = HOST_PREFIX + '/bin'
    HOST_INC = HOST_PREFIX + '/include/' + PYTHON_X_Y
    HOST_LIB = HOST_PREFIX + '/lib'
    HOST_PKG = HOST_LIB + '/' + PYTHON_X_Y

    PYTHON_PREFIX = APPDIR + '/opt/' + PYTHON_X_Y
    PYTHON_BIN = PYTHON_PREFIX + '/bin'
    PYTHON_INC = PYTHON_PREFIX + '/include/' + PYTHON_X_Y
    PYTHON_LIB = PYTHON_PREFIX + '/lib'
    PYTHON_PKG = PYTHON_LIB + '/' + PYTHON_X_Y

    if not os.path.exists(HOST_PKG):
        paths = glob.glob(HOST_PKG + '*')
        if paths:
            HOST_PKG = paths[0]
            PYTHON_PKG = PYTHON_LIB + '/' + os.path.basename(HOST_PKG)
        else:
            raise ValueError('could not find {0:}'.format(HOST_PKG))

    if not os.path.exists(HOST_INC):
        paths = glob.glob(HOST_INC + '*')
        if paths:
            HOST_INC = paths[0]
            PYTHON_INC = PYTHON_INC + '/' + os.path.basename(HOST_INC)
        else:
            raise ValueError('could not find {0:}'.format(HOST_INC))


    # Copy the running Python's install
    log('CLONE', '%s from %s', PYTHON_X_Y, HOST_PREFIX)

    source = HOST_BIN + '/' + PYTHON_X_Y
    if not os.path.exists(source):
        raise ValueError('could not find {0:} executable'.format(PYTHON_X_Y))
    make_tree(PYTHON_BIN)
    target = PYTHON_BIN + '/' + PYTHON_X_Y
    copy_file(source, target, update=True)

    copy_tree(HOST_PKG, PYTHON_PKG)
    copy_tree(HOST_INC, PYTHON_INC)

    make_tree(APPDIR_BIN)
    pip_source = HOST_BIN + '/' + PIP_X_Y
    if not os.path.exists(pip_source):
        pip_source = HOST_BIN + '/' + PIP_X
    if os.path.exists(pip_source):
        with open(pip_source) as f:
            f.readline()
            body = f.read()

        target = PYTHON_BIN + '/' + PIP_X_Y
        with open(target, 'w') as f:
            f.write('#! /bin/sh\n')
            f.write(' '.join((
                '"exec"',
                '"$(dirname $(readlink -f ${0}))/../../../usr/bin/' +
                    PYTHON_X_Y + '"',
                '"$0"',
                '"$@"\n'
            )))
            f.write(body)
        shutil.copymode(pip_source, target)


    # Remove unrelevant files
    log('PRUNE', '%s packages', PYTHON_X_Y)

    remove_file(PYTHON_LIB + '/lib' + PYTHON_X_Y + '.a')
    remove_tree(PYTHON_PKG + '/test')
    remove_file(PYTHON_PKG + '/dist-packages')
    matches = glob.glob(PYTHON_PKG + '/config-*-linux-*')
    for path in matches:
        remove_tree(path)


    # Set RPATHs and bundle external libraries
    log('LINK', '%s C-extensions', PYTHON_X_Y)

    make_tree(APPDIR_LIB)
    patch_binary(PYTHON_BIN + '/' + PYTHON_X_Y, APPDIR_LIB, recursive=False)
    for root, dirs, files in os.walk(PYTHON_PKG + '/lib-dynload'):
        for file_ in files:
            if not file_.endswith('.so'):
                continue
            patch_binary(os.path.join(root, file_), APPDIR_LIB, recursive=False)

    for file_ in glob.iglob(APPDIR_LIB + '/lib*.so*'):
        patch_binary(file_, APPDIR_LIB, recursive=True)


    # Copy shared data for TCl/Tk
    tk_version = _get_tk_version(PYTHON_PKG)
    if tk_version is not None:
        tcltkdir = APPDIR_SHARE + '/tcltk'
        if (not os.path.exists(tcltkdir + '/tcl' + tk_version)) or             \
           (not os.path.exists(tcltkdir + '/tk' + tk_version)):
            libdir = _get_tk_libdir(tk_version)
            log('INSTALL', 'Tcl/Tk' + tk_version)
            make_tree(tcltkdir)
            tclpath = libdir + '/tcl' + tk_version
            copy_tree(tclpath, tcltkdir + '/tcl' + tk_version)
            tkpath = libdir + '/tk' + tk_version
            copy_tree(tkpath, tcltkdir + '/tk' + tk_version)

    # Copy any SSL certificate
    cert_file = os.getenv('SSL_CERT_FILE')
    if cert_file:
        # Package certificates as well for SSL
        # (see https://github.com/niess/python-appimage/issues/24)
        dirname, basename = os.path.split(cert_file)
        make_tree('AppDir' + dirname)
        copy_file(cert_file, 'AppDir' + cert_file)
        log('INSTALL', basename)

    # Bundle AppImage specific files.
    appifier = Appifier(
        appdir = APPDIR,
        appdir_bin = APPDIR_BIN,
        python_bin = PYTHON_BIN,
        python_pkg = PYTHON_PKG,
        tk_version = tk_version,
        version = PythonVersion.from_str(FULLVERSION)
    )
    appifier.appify()


def _get_tk_version(python_pkg):
    tkinter = glob.glob(python_pkg + '/lib-dynload/_tkinter*.so')
    if tkinter:
        tkinter = tkinter[0]
        for dep in ldd(tkinter):
            name = os.path.basename(dep)
            if name.startswith('libtk'):
                match = re.search('libtk([0-9]+[.][0-9]+)', name)
                return match.group(1)
        else:
            raise RuntimeError('could not guess Tcl/Tk version')


def _get_tk_libdir(version):
    try:
        library = system(('tclsh' + version,), stdin='puts [info library]')
    except SystemError:
        raise RuntimeError('could not locate Tcl/Tk' + version + ' library')

    return os.path.dirname(library)
