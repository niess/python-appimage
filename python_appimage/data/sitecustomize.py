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


_bin_at_start = os.listdir(sys.prefix + '/bin')
'''Initial content of the bin/ directory
'''


def patch_pip_install():
    '''Change absolute shebangs to relative ones following a `pip` install
    '''
    if not 'pip' in sys.modules:
        return

    args = sys.argv[1:]
    if 'install' in args:
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
                continue

            if exe in _bin_at_start:
                continue

            usr_dir = os.path.join(sys.prefix, '../../usr/bin')
            usr_exe = os.path.join(usr_dir, exe)
            if not os.path.exists(usr_exe):
                relpath = os.path.relpath(path, usr_dir)
                os.symlink(relpath, usr_exe)

    elif 'uninstall' in args:
        usr_dir = os.path.join(sys.prefix, '../../usr/bin')
        for exe in os.listdir(usr_dir):
            path = os.path.join(usr_dir, exe)
            if (not os.path.islink(path)) or                                   \
               os.path.exists(os.path.realpath(path)):
                continue
            os.remove(path)


atexit.register(patch_pip_install)
