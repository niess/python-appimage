import glob
import os
import re
import shutil
import sys

from ..utils.deps import EXCLUDELIST, PATCHELF, PREFIX, ensure_excludelist,    \
                         ensure_patchelf
from ..utils.fs import make_tree, copy_file, copy_tree, remove_file, remove_tree
from ..utils.log import debug, log
from ..utils.system import ldd, system
from ..utils.template import copy_template


__all__ = ["patch_binary", "relocate_python"]


def _copy_template(name, destination, **kwargs):
    path = os.path.join(PREFIX, 'data', name)
    copy_template(path, destination, **kwargs)


_excluded_libs = None
'''Appimage excluded libraries, i.e. assumed to be installed on the host
'''


def patch_binary(path, libdir, recursive=True):
    '''Patch the RPATH of a binary and and fetch its dependencies
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

    ensure_patchelf()
    rpath = '\'' + system(PATCHELF, '--print-rpath', path) + '\''
    relpath = os.path.relpath(libdir, os.path.dirname(path))
    relpath = '' if relpath == '.' else '/' + relpath
    expected = '\'$ORIGIN' + relpath + '\''
    if rpath != expected:
        system(PATCHELF, '--set-rpath', expected, path)

    deps = ldd(path)
    for dep in deps:
        name = os.path.basename(dep)
        if name in excluded:
            continue
        target = libdir + '/' + name
        if not os.path.exists(target):
            libname = os.path.basename(dep)
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
        FULLVERSION = system(python, '-c',
            '"import sys; print(\'{:}.{:}.{:}\'.format(*sys.version_info[:3]))"')
        FULLVERSION = FULLVERSION.strip()
    else:
        FULLVERSION = '{:}.{:}.{:}'.format(*sys.version_info[:3])
    VERSION = '.'.join(FULLVERSION.split('.')[:2])
    PYTHON_X_Y = 'python' + VERSION

    APPDIR = os.path.abspath(appdir)
    APPDIR_BIN = APPDIR + '/usr/bin'
    APPDIR_LIB = APPDIR + '/usr/lib'
    APPDIR_SHARE = APPDIR + '/usr/share'

    if python:
        HOST_PREFIX = system(
            python, '-c', '"import sys; print(sys.prefix)"').strip()
    else:
        HOST_PREFIX = sys.prefix
    HOST_BIN = HOST_PREFIX + '/bin'
    HOST_INC = HOST_PREFIX + '/include/' + PYTHON_X_Y
    if not os.path.exists(HOST_INC):
        HOST_INC += 'm'
    HOST_LIB = HOST_PREFIX + '/lib'
    HOST_PKG = HOST_LIB + '/' + PYTHON_X_Y

    PYTHON_PREFIX = APPDIR + '/opt/' + PYTHON_X_Y
    PYTHON_BIN = PYTHON_PREFIX + '/bin'
    PYTHON_INC = PYTHON_PREFIX + '/include/' + PYTHON_X_Y
    PYTHON_LIB = PYTHON_PREFIX + '/lib'
    PYTHON_PKG = PYTHON_LIB + '/' + PYTHON_X_Y


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


    # Remove unrelevant files
    log('PRUNE', '%s packages', PYTHON_X_Y)

    remove_file(PYTHON_LIB + '/lib' + PYTHON_X_Y + '.a')
    remove_tree(PYTHON_PKG + '/test')
    remove_file(PYTHON_PKG + '/dist-packages')
    matches = glob.glob(PYTHON_PKG + '/config-*-linux-*')
    for path in matches:
        remove_tree(path)


    # Wrap the Python executable
    log('WRAP', '%s executable', PYTHON_X_Y)

    with open(PREFIX + '/data/python-wrapper.sh') as f:
        text = f.read()
    text = text.replace('{{PYTHON}}', PYTHON_X_Y)

    make_tree(APPDIR_BIN)
    target = APPDIR_BIN + '/' + PYTHON_X_Y
    with open(target, 'w') as f:
        f.write(text)
    shutil.copymode(PYTHON_BIN + '/' + PYTHON_X_Y, target)


    # Set a hook in Python for cleaning the path detection
    log('HOOK', '%s site packages', PYTHON_X_Y)

    sitepkgs = PYTHON_PKG + '/site-packages'
    make_tree(sitepkgs)
    copy_file(PREFIX + '/data/sitecustomize.py', sitepkgs)


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
    tkinter = glob.glob(PYTHON_PKG + '/lib-dynload/_tkinter*.so')
    if tkinter:
        tkinter = tkinter[0]
        for dep in ldd(tkinter):
            name = os.path.basename(dep)
            if name.startswith('libtk'):
                match = re.search('libtk([0-9]+[.][0-9]+)', name)
                tk_version = match.group(1)
                break
        else:
            raise RuntimeError('could not guess Tcl/Tk version')

        tcltkdir = APPDIR_SHARE + '/tcltk'
        if (not os.path.exists(tcltkdir + '/tcl' + tk_version)) or             \
           (not os.path.exists(tcltkdir + '/tk' + tk_version)):
            hostdir = '/usr/share/tcltk'
            if os.path.exists(hostdir):
                make_tree(APPDIR_SHARE)
                copy_tree(hostdir, tcltkdir)
            else:
                make_tree(tcltkdir)
                tclpath = '/usr/share/tcl' + tk_version
                if not tclpath:
                    raise ValueError('could not find ' + tclpath)
                copy_tree(tclpath, tcltkdir + '/tcl' + tk_version)

                tkpath = '/usr/share/tk' + tk_version
                if not tkpath:
                    raise ValueError('could not find ' + tkpath)
                copy_tree(tkpath, tcltkdir + '/tk' + tk_version)


    # Bundle the entry point
    apprun = APPDIR + '/AppRun'
    if not os.path.exists(apprun):
        log('INSTALL', 'AppRun')
        entrypoint = '"${{APPDIR}}/usr/bin/python{:}" "$@"'.format(VERSION)
        _copy_template('apprun.sh', apprun, entrypoint=entrypoint)


    # Bundle the desktop file
    desktop_name = 'python{:}.desktop'.format(FULLVERSION)
    desktop = os.path.join(APPDIR, desktop_name)
    if not os.path.exists(desktop):
        log('INSTALL', desktop_name)
        apps = 'usr/share/applications'
        appfile = '{:}/{:}/python{:}.desktop'.format(APPDIR, apps, FULLVERSION)
        if not os.path.exists(appfile):
            make_tree(os.path.join(APPDIR, apps))
            _copy_template('python.desktop', appfile, version=VERSION,
                                                      fullversion=FULLVERSION)
        os.symlink(os.path.join(apps, desktop_name), desktop)


    # Bundle icons
    icons = 'usr/share/icons/hicolor/256x256/apps'
    icon = os.path.join(APPDIR, 'python.png')
    if not os.path.exists(icon):
        log('INSTALL', 'python.png')
        make_tree(os.path.join(APPDIR, icons))
        copy_file(PREFIX + '/data/python.png',
                  os.path.join(APPDIR, icons, 'python.png'))
        os.symlink(os.path.join(icons, 'python.png'), icon)

    diricon = os.path.join(APPDIR, '.DirIcon')
    if not os.path.exists(diricon):
        os.symlink('python.png', diricon)


    # Bundle metadata
    meta_name = 'python{:}.appdata.xml'.format(FULLVERSION)
    meta_dir = os.path.join(APPDIR, 'usr/share/metainfo')
    meta_file = os.path.join(meta_dir, meta_name)
    if not os.path.exists(meta_file):
        log('INSTALL', meta_name)
        make_tree(meta_dir)
        _copy_template('python.appdata.xml', meta_file, version=VERSION,
                                                        fullversion=FULLVERSION)
