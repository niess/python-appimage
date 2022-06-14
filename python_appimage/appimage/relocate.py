import glob
import os
import re
import shutil
import sys

from ..utils.deps import EXCLUDELIST, PATCHELF, PREFIX, ensure_excludelist,    \
                         ensure_patchelf
from ..utils.fs import copy_file, copy_tree, make_tree, remove_file, remove_tree
from ..utils.log import debug, log
from ..utils.system import ldd, system
from ..utils.template import copy_template, load_template


__all__ = ["cert_file_env_string", "patch_binary", "relocate_python",
           "tcltk_env_string"]


def _copy_template(name, destination, **kwargs):
    path = os.path.join(PREFIX, 'data', name)
    copy_template(path, destination, **kwargs)


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


def tcltk_env_string(python_pkg):
    '''Environment for using AppImage's TCl/Tk
    '''
    tk_version = _get_tk_version(python_pkg)

    if tk_version:
        return '''
# Export TCl/Tk
export TCL_LIBRARY="${{APPDIR}}/usr/share/tcltk/tcl{tk_version:}"
export TK_LIBRARY="${{APPDIR}}/usr/share/tcltk/tk{tk_version:}"
export TKPATH="${{TK_LIBRARY}}"'''.format(
    tk_version=tk_version)
    else:
        return ''


def cert_file_env_string(cert_file):
    '''Environment for using a bundled certificate
    '''
    if cert_file:
        return '''
# Export SSL certificate
export SSL_CERT_FILE="${{APPDIR}}{cert_file:}"'''.format(
    cert_file=cert_file)
    else:
        return ''


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
    rpath = '\'' + system((PATCHELF, '--print-rpath', path)) + '\''
    relpath = os.path.relpath(libdir, os.path.dirname(path))
    relpath = '' if relpath == '.' else '/' + relpath
    expected = '\'$ORIGIN' + relpath + '\''
    if rpath != expected:
        system((PATCHELF, '--set-rpath', expected, path))

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


def set_executable_patch(version, pkgpath, patch):
    '''Set a runtime patch for sys.executable name
    '''

    # This patch needs to be executed before site.main() is called. A natural
    # option is to apply it directy to the site module. But, starting with
    # Python 3.11, the site module is frozen within Python executable. Then,
    # doing so would require to recompile Python. Thus, starting with 3.11 we
    # instead apply the patch to the encodings package. Indeed, the latter is
    # loaded before the site module, and it is not frozen (as for now).
    major, minor = [int(v) for v in version.split('.')]
    if (major >= 3) and (minor >= 11):
        path = os.path.join(pkgpath, 'encodings', '__init__.py')
    else:
        path = os.path.join(pkgpath, 'site.py')

    with open(path) as f:
        source = f.read()

    if '_initappimage' in source: return

    lines = source.split(os.linesep)

    if path.endswith('site.py'):
        # Insert the patch before the main function
        for i, line in enumerate(lines):
            if line.startswith('def main('): break
    else:
        # Append the patch at end of file
        i = len(lines)

    with open(patch) as f:
        patch = f.read()

    lines.insert(i, patch)
    lines.insert(i + 1, '')

    source = os.linesep.join(lines)
    with open(path, 'w') as f:
        f.write(source)


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
        FULLVERSION = system((python, '-c',
            '"import sys; print(\'{:}.{:}.{:}\'.format(*sys.version_info[:3]))"'))
        FULLVERSION = FULLVERSION.strip()
    else:
        FULLVERSION = '{:}.{:}.{:}'.format(*sys.version_info[:3])
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

    if not os.path.exists(HOST_INC):
        HOST_INC += 'm'
        PYTHON_INC += 'm'


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

        relpath = os.path.relpath(target, APPDIR_BIN)
        os.symlink(relpath, APPDIR_BIN + '/' + PIP_X_Y)


    # Remove unrelevant files
    log('PRUNE', '%s packages', PYTHON_X_Y)

    remove_file(PYTHON_LIB + '/lib' + PYTHON_X_Y + '.a')
    remove_tree(PYTHON_PKG + '/test')
    remove_file(PYTHON_PKG + '/dist-packages')
    matches = glob.glob(PYTHON_PKG + '/config-*-linux-*')
    for path in matches:
        remove_tree(path)

    # Add a runtime patch for sys.executable, before site.main() execution
    log('PATCH', '%s sys.executable', PYTHON_X_Y)
    set_executable_patch(VERSION, PYTHON_PKG, PREFIX + '/data/_initappimage.py')

    # Set a hook for cleaning sys.path, after site.main() execution
    log('HOOK', '%s sys.path', PYTHON_X_Y)

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
    tk_version = _get_tk_version(PYTHON_PKG)
    if tk_version is not None:
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


    # Copy any SSL certificate
    cert_file = os.getenv('SSL_CERT_FILE')
    if cert_file:
        # Package certificates as well for SSL
        # (see https://github.com/niess/python-appimage/issues/24)
        dirname, basename = os.path.split(cert_file)
        make_tree('AppDir' + dirname)
        copy_file(cert_file, 'AppDir' + cert_file)
        log('INSTALL', basename)


    # Bundle the python wrapper
    wrapper = APPDIR_BIN + '/' + PYTHON_X_Y
    if not os.path.exists(wrapper):
        log('INSTALL', '%s wrapper', PYTHON_X_Y)
        entrypoint_path = PREFIX + '/data/entrypoint.sh'
        entrypoint = load_template(entrypoint_path, python=PYTHON_X_Y)
        dictionary = {'entrypoint': entrypoint,
                      'shebang': '#! /bin/bash',
                      'tcltk-env': tcltk_env_string(PYTHON_PKG),
                      'cert-file': cert_file_env_string(cert_file)}
        _copy_template('python-wrapper.sh', wrapper, **dictionary)

    # Set or update symlinks to python
    pythons = glob.glob(APPDIR_BIN + '/python?.*')
    versions = [os.path.basename(python)[6:] for python in pythons]
    latest2, latest3 = '0.0', '0.0'
    for version in versions:
        if version.startswith('2') and version >= latest2:
            latest2 = version
        elif version.startswith('3') and version >= latest3:
            latest3 = version
    if latest2 == VERSION:
        python2 = APPDIR_BIN + '/python2'
        remove_file(python2)
        os.symlink(PYTHON_X_Y, python2)
        has_pip = os.path.exists(APPDIR_BIN + '/' + PIP_X_Y)
        if has_pip:
            pip2 = APPDIR_BIN + '/pip2'
            remove_file(pip2)
            os.symlink(PIP_X_Y, pip2)
        if latest3 == '0.0':
            log('SYMLINK', 'python, python2 to ' + PYTHON_X_Y)
            python = APPDIR_BIN + '/python'
            remove_file(python)
            os.symlink('python2', python)
            if has_pip:
                log('SYMLINK', 'pip, pip2 to ' + PIP_X_Y)
                pip = APPDIR_BIN + '/pip'
                remove_file(pip)
                os.symlink('pip2', pip)
        else:
            log('SYMLINK', 'python2 to ' + PYTHON_X_Y)
            if has_pip:
                log('SYMLINK', 'pip2 to ' + PIP_X_Y)
    elif latest3 == VERSION:
        log('SYMLINK', 'python, python3 to ' + PYTHON_X_Y)
        python3 = APPDIR_BIN + '/python3'
        remove_file(python3)
        os.symlink(PYTHON_X_Y, python3)
        python = APPDIR_BIN + '/python'
        remove_file(python)
        os.symlink('python3', python)
        if os.path.exists(APPDIR_BIN + '/' + PIP_X_Y):
            log('SYMLINK', 'pip, pip3 to ' + PIP_X_Y)
            pip3 = APPDIR_BIN + '/pip3'
            remove_file(pip3)
            os.symlink(PIP_X_Y, pip3)
            pip = APPDIR_BIN + '/pip'
            remove_file(pip)
            os.symlink('pip3', pip)

    # Bundle the entry point
    apprun = APPDIR + '/AppRun'
    if not os.path.exists(apprun):
        log('INSTALL', 'AppRun')

        relpath = os.path.relpath(wrapper, APPDIR)
        os.symlink(relpath, APPDIR + '/AppRun')

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
