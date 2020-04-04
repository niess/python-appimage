'''Hooks for isloating the AppImage Python and making it relocatable
'''
import atexit
import os
import sys


def clean_path():
    '''Remove system locations from the packages search path
    '''
    site_packages = '/usr/local/lib/python{:}.{:}/site-packages'.format(
        *sys.version_info[:2])
    binaries_path = '/usr/local/bin'
    env_path = os.getenv("PYTHONPATH")
    if env_path is None:
        env_path = []
    else:
        env_path = [os.path.realpath(path) for path in env_path.split(':')]

    if ((os.path.dirname(sys.executable) != binaries_path) and
        (site_packages not in env_path)):
        # Remove the builtin site-packages from the path
        try:
            sys.path.remove(site_packages)
        except ValueError:
            pass


clean_path()


def patch_pip_install():
    '''Change absolute shebangs to relative ones following a `pip` install
    '''
    if ('pip' in sys.modules) and ('install' in sys.argv[1:]):
        for exe in os.listdir(sys.prefix + '/bin'):
            path = os.path.join(sys.prefix, 'bin', exe)

            if (not os.path.isfile(path)) or (not os.access(path, os.X_OK)) or \
               exe.startswith('python') or os.path.islink(path) or             \
               exe.endswith('.pyc') or exe.endswith('.pyo'):
                continue

            try:
                with open(path, 'r') as f:
                    header = f.read(2)
                    if header != '#!':
                        continue
                    content = f.read()
            except:
                continue

            shebang, body = content.split(os.linesep, 1)
            shebang = shebang.split()
            python_x_y = os.path.basename(shebang.pop(0))
            if not python_x_y.startswith('python'):
                continue

            relpath = os.path.relpath(
                sys.prefix + '/../../usr/bin/' + python_x_y,
                sys.prefix + '/bin')
            shebang.append('"$@"')
            cmd = (
                '"exec"',
                '"$(dirname $(readlink -f ${0}))/' + relpath + '"',
                '"$0"',
                ' '.join(shebang)
            )

            try:
                with open(path, 'w') as f:
                    f.write('#! /bin/sh\n')
                    f.write(' '.join(cmd) + '\n')
                    f.write(body)
            except IOError:
                pass


atexit.register(patch_pip_install)
