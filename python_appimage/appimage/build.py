import os
import platform
import re
import subprocess
import sys

from ..utils.compat import decode
from ..utils.deps import ensure_appimagetool
from ..utils.log import debug, log


__all__ = ['build_appimage']


def build_appimage(appdir=None, *, arch=None, destination=None):
    '''Build an AppImage from an AppDir
    '''
    if appdir is None:
        appdir = 'AppDir'

    log('BUILD', os.path.basename(appdir))
    appimagetool = ensure_appimagetool()

    if arch is None:
        arch = platform.machine()
    cmd = ['ARCH=' + arch, appimagetool, '--no-appstream', appdir]
    if destination is not None:
        cmd.append(destination)
    cmd = ' '.join(cmd)

    debug('SYSTEM', cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT)

    appimage_pattern = re.compile('should be packaged as ([^ ]+[.]AppImage)')

    stdout = []
    while True:
        out = decode(p.stdout.readline())
        stdout.append(out)
        if out == '' and p.poll() is not None:
            break
        elif out:
            out = out.replace('%', '%%')[:-1]
            for line in out.split(os.linesep):
                if line.startswith('WARNING') and \
                    not line[9:].startswith('zsyncmake command is missing'):
                    log('WARNING', line[9:])
                elif line.startswith('Error'):
                    raise RuntimeError(line)
                else:
                    if destination is None:
                        match = appimage_pattern.search(line)
                        if match is not None:
                            destination = match.group(1)
                    debug('APPIMAGE', line)

    rc = p.poll()
    if rc != 0 and not os.path.exists(destination):
        print(''.join(stdout))
        sys.stdout.flush()
        raise RuntimeError('Could not build AppImage')
