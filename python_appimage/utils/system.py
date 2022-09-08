import os
import re
import subprocess

from .compat import decode, encode
from .log import debug, log


__all__ = ['ldd', 'system']


try:
    basestring
except NameError:
    basestring = (str, bytes)


def system(args, exclude=None, stdin=None):
    '''System call with capturing output
    '''
    cmd = ' '.join(args)
    debug('SYSTEM', cmd)

    if exclude is None:
        exclude = []
    elif isinstance(exclude, basestring):
        exclude = [exclude]
    else:
        exclude = list(exclude)
    exclude.append('fuse: warning:')

    if stdin:
        in_arg = subprocess.PIPE
        stdin = encode(stdin)
    else:
        in_arg = None

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, stdin=in_arg)
    out, err = p.communicate(input=stdin)
    if err:
        err = decode(err)
        stripped = [line for line in err.split(os.linesep) if line]
        for pattern in exclude:
            stripped = [line for line in stripped
                        if not line.startswith(pattern)]
        if stripped:
            # Tolerate single line warning(s)
            for line in stripped:
                if (len(line) < 8) or (line[:8].lower() != "warning:"):
                    raise RuntimeError(err)
            else:
                for line in stripped:
                    log('WARNING', line[8:].strip())

    return str(decode(out).strip())


_ldd_pattern = re.compile('=> (.+) [(]0x')


def ldd(path):
    '''Get dependencies list of dynamic libraries
    '''
    out = system(('ldd', path))
    return _ldd_pattern.findall(out)
