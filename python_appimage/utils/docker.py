import os
import platform
import stat
import subprocess
import sys

from .log import log
from .system import system


def docker_run(image, extra_cmds):
    '''Execute commands within a docker container
    '''

    ARCH = platform.machine()
    if image.endswith(ARCH):
        bash_arg = '/pwd/run.sh'
    elif image.endswith('i686') and ARCH == 'x86_64':
        bash_arg = '-c "linux32 /pwd/run.sh"'
    elif image.endswith('x86_64') and ARCH == 'i686':
        bash_arg = '-c "linux64 /pwd/run.sh"'
    else:
        raise ValueError('Unsupported Docker image: ' + image)

    log('PULL', image)
    system(('docker', 'pull', image))

    script = [
        'set -e',
        'trap "chown -R {:}:{:} *" EXIT'.format(os.getuid(),
                                                os.getgid()),
        'cd /pwd'
    ]

    script += extra_cmds

    with open('run.sh', 'w') as f:
        f.write(os.linesep.join(script))
    os.chmod('run.sh', stat.S_IRWXU)

    cmd = ' '.join(('docker', 'run', '--mount',
                    'type=bind,source={:},target=/pwd'.format(os.getcwd()),
                    image, '/bin/bash', bash_arg))

    log('RUN', image)
    p = subprocess.Popen(cmd, shell=True)
    p.communicate()
    if p.returncode != 0:
        if p.returncode == 139:
            sys.stderr.write("segmentation fault when running Docker (139)\n")
        sys.exit(p.returncode)
