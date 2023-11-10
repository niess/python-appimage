import os

from ..utils.docker import docker_run
from ..utils.log import log
from ..utils.tmp import TemporaryDirectory


__all__ = ['execute']


def _unpack_args(args):
    '''Unpack command line arguments
    '''
    return (args.tag,)


def execute(tag):
    '''List python versions installed in a manylinux image
    '''

    with TemporaryDirectory() as tmpdir:
        script = (
            'for dir in $(ls /opt/python | grep "^cp[0-9]"); do',
            '   version=$(/opt/python/$dir/bin/python -c "import sys; ' \
                    'sys.stdout.write(sys.version.split()[0])")',
            '   echo "$dir $version"',
            'done',
        )
        if tag.startswith('2_'):
            image = 'manylinux_' + tag
        else:
            image = 'manylinux' + tag
        result = docker_run(
            'quay.io/pypa/' + image,
            script,
            capture = True
        )
        pythons = [line.split() for line in result.split(os.linesep) if line]

        for (abi, version) in pythons:
            log('LIST', "{:7} ->  /opt/python/{:}".format(version, abi))

        return pythons
