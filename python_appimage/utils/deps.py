import os
import platform
import stat

from .fs import copy_file, copy_tree, make_tree
from .log import log
from .system import system
from .tmp import TemporaryDirectory
from .url import urlretrieve


_ARCH = platform.machine()

CACHE_DIR = os.path.expanduser('~/.cache/python-appimage')
'''Package cache location'''

PREFIX = os.path.abspath(os.path.dirname(__file__) + '/..')
'''Package installation prefix'''

APPIMAGETOOL_DIR = os.path.join(CACHE_DIR, 'bin')
'''Location of the appimagetool binary'''

APPIMAGETOOL_VERSION = 'continuous'
'''Version of the appimagetool binary'''

EXCLUDELIST = os.path.join(CACHE_DIR, 'share/excludelist')
'''AppImage exclusion list'''

PATCHELF = os.path.join(CACHE_DIR, 'bin/patchelf')
'''Location of the PatchELF binary'''

PATCHELF_VERSION = '0.14.3'
'''Version of the patchelf binary'''


def ensure_appimagetool(dry=False):
    '''Fetch appimagetool from the web if not available locally
    '''

    if APPIMAGETOOL_VERSION == '12':
        appimagetool_name = 'appimagetool'
    else:
        appimagetool_name = 'appimagetool-' + APPIMAGETOOL_VERSION
    appdir_name = '.'.join(('', appimagetool_name, 'appdir', _ARCH))
    appdir = os.path.join(APPIMAGETOOL_DIR, appdir_name)
    apprun = os.path.join(appdir, 'AppRun')

    if dry or os.path.exists(apprun):
        return apprun
    appimage = 'appimagetool-{0:}.AppImage'.format(_ARCH)

    if APPIMAGETOOL_VERSION in map(str, range(1, 14)):
        repository = 'AppImageKit'
    else:
        repository = 'appimagetool'
    baseurl = os.path.join(
        'https://github.com/AppImage',
        repository,
        'releases/download',
        APPIMAGETOOL_VERSION
    )
    log('INSTALL', 'appimagetool from %s', baseurl)

    if not os.path.exists(appdir):
        make_tree(os.path.dirname(appdir))
        with TemporaryDirectory() as tmpdir:
            urlretrieve(os.path.join(baseurl, appimage), appimage)
            os.chmod(appimage, stat.S_IRWXU)
            system(('./' + appimage, '--appimage-extract'))
            copy_tree('squashfs-root', appdir)

    return apprun


# Installers for dependencies
def ensure_excludelist():
    '''Fetch the AppImage excludelist from the web if not available locally
    '''
    if os.path.exists(EXCLUDELIST):
        return

    baseurl = 'https://raw.githubusercontent.com/probonopd/AppImages/master'
    log('INSTALL', 'excludelist from %s', baseurl)
    urlretrieve(baseurl + '/excludelist', EXCLUDELIST)
    mode = os.stat(EXCLUDELIST)[stat.ST_MODE]
    os.chmod(EXCLUDELIST, mode | stat.S_IWGRP | stat.S_IWOTH)


def ensure_patchelf():
    '''Fetch PatchELF from the web if not available locally
    '''
    if os.path.exists(PATCHELF):
        return False

    tgz = '-'.join(('patchelf', PATCHELF_VERSION, _ARCH)) + '.tar.gz'
    baseurl = 'https://github.com/NixOS/patchelf'
    log('INSTALL', 'patchelf from %s', baseurl)

    dirname = os.path.dirname(PATCHELF)
    patchelf = dirname + '/patchelf'
    make_tree(dirname)
    with TemporaryDirectory() as tmpdir:
        urlretrieve(os.path.join(baseurl, 'releases', 'download',
                                 PATCHELF_VERSION, tgz), tgz)
        system(('tar', 'xzf', tgz))
        copy_file('bin/patchelf', patchelf)
    os.chmod(patchelf, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    return True
