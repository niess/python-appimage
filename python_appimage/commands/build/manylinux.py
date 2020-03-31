import glob
import os
import platform
import shutil
import sys

from ...appimage import build_appimage, relocate_python
from ...utils.docker import docker_run
from ...utils.fs import copy_tree
from ...utils.tmp import TemporaryDirectory


__all__ = ['execute']


def _unpack_args(args):
    '''Unpack command line arguments
    '''
    return args.tag, args.abi, args.contained


def _get_appimage_name(abi, tag):
    '''Format the Python AppImage name using the ABI and OS tags
    '''
    # Read the Python version from the desktop file
    desktop = glob.glob('AppDir/python*.desktop')[0]
    fullversion = desktop[13:-8]

    # Finish building the AppImage on the host. See below.
    return 'python{:}-{:}-manylinux{:}.AppImage'.format(
        fullversion, abi, tag)


def execute(tag, abi, contained=False):
    '''Build a Python AppImage using a manylinux docker image
    '''

    if not contained:
        # Forward the build to a Docker image
        image = 'quay.io/pypa/manylinux' + tag
        python = '/opt/python/' + abi + '/bin/python'

        pwd = os.getcwd()
        dirname = os.path.abspath(os.path.dirname(__file__) + '/../..')
        with TemporaryDirectory() as tmpdir:
            copy_tree(dirname, 'python_appimage')

            argv = ' '.join(sys.argv[1:])
            script = (
                'yum --disablerepo="*" --enablerepo=base install -q -y tk',
                python + ' -m python_appimage ' + argv + ' --contained',
                ''
            )
            docker_run(image, script)

            appimage_name = _get_appimage_name(abi, tag)

            if tag.startswith('1_'):
                # appimagetool does not run on manylinux1 (CentOS 5). Below is
                # a patch for this specific case.
                arch = tag.split('_', 1)[-1]
                if arch == platform.machine():
                    # Pack the image directly from the host
                    build_appimage(destination=appimage_name)
                else:
                    # Use a manylinux2010 Docker image (CentOS 6) in order to
                    # pack the image.
                    script = (
                        python + ' -m python_appimage ' + argv + ' --contained',
                        ''
                    )
                    docker_run('quay.io/pypa/manylinux2010_' + arch, script)

            shutil.move(appimage_name, os.path.join(pwd, appimage_name))

    else:
        # We are running within a manylinux Docker image
        is_manylinux1 = tag.startswith('1_')

        if not os.path.exists('AppDir'):
            # Relocate the targeted manylinux Python installation
            relocate_python()
        else:
            # This is a second stage build. The Docker image has actually been
            # overriden (see above).
            is_manylinux1 = False

        if is_manylinux1:
            # Build only the AppDir when running within a manylinux1 Docker
            # image because appimagetool does not support CentOS 5.
            pass
        else:
            build_appimage(destination=_get_appimage_name(abi, tag))
