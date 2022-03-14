import os
import platform
import stat

from .fs import copy_file, copy_tree, make_tree
from .log import log
from .system import system
from .tmp import TemporaryDirectory
from .url import urlretrieve


__all__ = ['APPIMAGETOOL', 'EXCLUDELIST', 'PATCHELF', 'PREFIX',
           'ensure_appimagetool', 'ensure_excludelist', 'ensure_patchelf']


_ARCH = platform.machine()


PREFIX = os.path.abspath(os.path.dirname(__file__) + '/..')
'''Package installation prefix'''

APPIMAGETOOL = os.path.expanduser('~/.local/bin/appimagetool')
'''Location of the appimagetool binary'''

EXCLUDELIST = PREFIX + '/data/excludelist'
'''AppImage exclusion list'''

PATCHELF = os.path.expanduser('~/.local/bin/patchelf')
'''Location of the PatchELF binary'''


def ensure_appimagetool():
    '''Fetch appimagetool from the web if not available locally
    '''
    if os.path.exists(APPIMAGETOOL):
        return False

    appimage = 'appimagetool-{0:}.AppImage'.format(_ARCH)
    baseurl = 'https://github.com/AppImage/AppImageKit/releases/'              \
              'download/12'
    log('INSTALL', 'appimagetool from %s', baseurl)

    appdir_name = '.appimagetool.appdir'.format(_ARCH)
    appdir = os.path.join(os.path.dirname(APPIMAGETOOL), appdir_name)
    if not os.path.exists(appdir):
        make_tree(os.path.dirname(appdir))
        with TemporaryDirectory() as tmpdir:
            urlretrieve(os.path.join(baseurl, appimage), appimage)
            os.chmod(appimage, stat.S_IRWXU)
            system(('./' + appimage, '--appimage-extract'))
            copy_tree('squashfs-root', appdir)

    if not os.path.exists(APPIMAGETOOL):
        os.symlink(appdir_name + '/AppRun', APPIMAGETOOL)

    return True


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

    iarch = 'i386' if _ARCH == 'i686' else _ARCH
    appimage = 'patchelf-{0:}.AppImage'.format(iarch)
    baseurl = 'https://github.com/niess/patchelf.appimage/releases/download'
    log('INSTALL', 'patchelf from %s', baseurl)

    dirname = os.path.dirname(PATCHELF)
    patchelf = dirname + '/patchelf'
    make_tree(dirname)
    with TemporaryDirectory() as tmpdir:
        urlretrieve(os.path.join(baseurl, 'rolling', appimage), appimage)
        os.chmod(appimage, stat.S_IRWXU)
        system(('./' + appimage, '--appimage-extract'))
        copy_file('squashfs-root/usr/bin/patchelf', patchelf)
    os.chmod(patchelf, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    return True
