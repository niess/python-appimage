import os
import re
import subprocess

from .log import debug


__all__ = ['ldd', 'system']


def _decode(s):
    '''Decode Python 3 bytes as str
    '''
    try:
        return s.decode()
    except AttributeError:
        return s


def system(*args):
    '''System call with capturing output
    '''
    cmd = ' '.join(args)
    debug('SYSTEM', cmd)

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err:
        err = _decode(err)
        stripped = [line for line in err.split(os.linesep)
                    if line and not line.startswith('fuse: warning:')]
        if stripped:
            raise RuntimeError(err)

    return str(_decode(out).strip())


_ldd_pattern = re.compile('=> (.+) [(]0x')


def ldd(path):
    '''Get dependencies list of dynamic libraries
    '''
    out = system('ldd', path)
    return _ldd_pattern.findall(out)
