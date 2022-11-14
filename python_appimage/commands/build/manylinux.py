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


def _manylinux_tag(tag):
    '''Format Manylinux tag
    '''
    if tag.startswith('2_'):
        return 'manylinux_' + tag
    else:
        return 'manylinux' + tag


def _get_appimage_name(abi, tag):
    '''Format the Python AppImage name using the ABI and OS tags
    '''
    # Read the Python version from the desktop file
    desktop = glob.glob('AppDir/python*.desktop')[0]
    fullversion = desktop[13:-8]

    # Finish building the AppImage on the host. See below.
    return 'python{:}-{:}-{:}.AppImage'.format(
        fullversion, abi, _manylinux_tag(tag))


def execute(tag, abi, contained=False):
    '''Build a Python AppImage using a manylinux docker image
    '''

    if not contained:
        # Forward the build to a Docker image
        image = 'quay.io/pypa/' + _manylinux_tag(tag)
        python = '/opt/python/' + abi + '/bin/python'

        pwd = os.getcwd()
        dirname = os.path.abspath(os.path.dirname(__file__) + '/../..')
        with TemporaryDirectory() as tmpdir:
            copy_tree(dirname, 'python_appimage')

            argv = ' '.join(sys.argv[1:])
            if tag.startswith("1_"):
                # On manylinux1 tk is not installed
                script = [
                    'yum --disablerepo="*" --enablerepo=base install -q -y tk']
            else:
                # tk is already installed on other platforms
                script = []
            script += [
                python + ' -m python_appimage ' + argv + ' --contained',
                ''
            ]
            docker_run(image, script)

            appimage_name = _get_appimage_name(abi, tag)

            if tag.startswith('1_') or tag.startswith('2010_'):
                # appimagetool does not run on manylinux1 (CentOS 5) or
                # manylinux2010 (CentOS 6). Below is a patch for these specific
                # cases.
                arch = tag.split('_', 1)[-1]
                if arch == platform.machine():
                    # Pack the image directly from the host
                    build_appimage(destination=appimage_name)
                else:
                    # Use a manylinux2014 Docker image (CentOS 7) in order to
                    # pack the image.
                    script = (
                        'python -m python_appimage ' + argv + ' --contained',
                        ''
                    )
                    docker_run('quay.io/pypa/manylinux2014_' + arch, script)

            shutil.move(appimage_name, os.path.join(pwd, appimage_name))

    else:
        # We are running within a manylinux Docker image
        is_manylinux_old = tag.startswith('1_') or tag.startswith('2010_')

        if not os.path.exists('AppDir'):
            # Relocate the targeted manylinux Python installation
            relocate_python()
        else:
            # This is a second stage build. The Docker image has actually been
            # overriden (see above).
            is_manylinux_old = False

        if is_manylinux_old:
            # Build only the AppDir when running within a manylinux1 Docker
            # image because appimagetool does not support CentOS 5 or CentOS 6.
            pass
        else:
            build_appimage(destination=_get_appimage_name(abi, tag))
