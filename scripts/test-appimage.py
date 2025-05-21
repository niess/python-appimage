#! /usr/bin/env python3
import argparse
import inspect
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import NamedTuple


from python_appimage.manylinux import PythonVersion


ARGS = None


def assert_eq(expected, found):
    if expected != found:
        raise AssertionError('expected "{}", found "{}"'.format(
            expected, found))


class Script(NamedTuple):
    '''Python script wrapper'''

    content: str

    def run(self, appimage: Path):
        '''Run the script through an appimage'''

        with tempfile.TemporaryDirectory() as tmpdir:
            script = f'{tmpdir}/script.py'
            with open(script, 'w') as f:
                f.write(inspect.getsource(assert_eq))
                f.write(os.linesep)
                f.write(self.content)
            return system(f'{appimage} {script}')


def system(cmd):
    '''Run a system command'''

    r = subprocess.run(cmd, capture_output=True, shell=True)

    if r.returncode != 0:
        raise ValueError(r.stderr.decode())
    else:
        return r.stdout.decode()


def test():
    '''Test Python AppImage(s)'''

    for appimage in ARGS.appimage:

        # Guess python version from appimage name.
        version, _, abi, *_ = appimage.name.split('-', 3)
        version = version[6:]
        if abi.endswith('t'):
            version += '-nogil'
        version = PythonVersion.from_str(version)

        # Get some specific AppImage env variables.
        env = eval(Script('''
import os
appdir = os.environ['APPDIR']
env = {}
for var in ('SSL_CERT_FILE', 'TCL_LIBRARY', 'TK_LIBRARY', 'TKPATH'):
    env[var] = os.environ[var].replace(appdir, '$APPDIR')
print(env)
        ''').run(appimage))

        # Extract the AppImage.
        tmpdir = tempfile.TemporaryDirectory()
        dst = Path(tmpdir.name) / appimage.name
        shutil.copy(appimage, dst)
        system(f'cd {tmpdir.name} && ./{appimage.name} --appimage-extract')
        appdir = Path(tmpdir.name) / 'squashfs-root'

        def list_content(path=None):
            path = appdir if path is None else appdir / path
            return sorted(os.listdir(path))

        # Check the appimage root content.
        content = list_content()
        expected = ['.DirIcon', 'AppRun', 'opt', 'python.png',
                    f'python{version.long()}.desktop', 'usr']
        assert_eq(expected, content)

        # Check the appimage python content.
        prefix = f'opt/python{version.flavoured()}'
        content = list_content(prefix)
        assert_eq(['bin', 'include', 'lib'], content)
        content = list_content(f'{prefix}/bin')
        assert_eq(
            [f'pip{version.short()}', f'python{version.flavoured()}'],
            content
        )
        content = list_content(f'{prefix}/include')
        assert_eq([f'python{version.flavoured()}'], content)
        content = list_content(f'{prefix}/lib')
        assert_eq([f'python{version.flavoured()}'], content)

        # Check the appimage system content.
        content = list_content('usr')
        assert_eq(['bin', 'lib', 'share'], content)
        content = list_content('usr/bin')
        expected = ['pip', f'pip{version.major}', f'pip{version.short()}',
                    'python', f'python{version.major}',
                    f'python{version.short()}']
        assert_eq(expected, content)

        # Check Tcl/Tk bundling.
        for var in ('TCL_LIBRARY', 'TK_LIBRARY', 'TKPATH'):
            assert Path(env[var].replace('$APPDIR', str(appdir))).exists()

        # Check SSL certs bundling.
        var = 'SSL_CERT_FILE'
        assert Path(env[var].replace('$APPDIR', str(appdir))).exists()

        # Check /usr/bin symlinks.
        assert_eq(
            (appdir /
             f'opt/python{version.flavoured()}/bin/pip{version.short()}'),
            (appdir / f'usr/bin/pip{version.short()}').resolve()
        )
        assert_eq(
            f'pip{version.short()}',
            str((appdir / f'usr/bin/pip{version.major}').readlink())
        )
        assert_eq(
            f'pip{version.major}',
            str((appdir / 'usr/bin/pip').readlink())
        )
        assert_eq(
            f'python{version.short()}',
            str((appdir / f'usr/bin/python{version.major}').readlink())
        )
        assert_eq(
            f'python{version.major}',
            str((appdir / 'usr/bin/python').readlink())
        )

        # Test the appimage hook.
        Script(f'''
import os
assert_eq(os.environ['APPIMAGE_COMMAND'], '{appimage}')

import sys
assert_eq('{appimage}', sys.executable)
assert_eq('{appimage}', sys._base_executable)
        ''').run(appimage)

        # Test the python prefix.
        Script(f'''
import os
import sys
expected = os.environ["APPDIR"] + '/opt/python{version.flavoured()}'
assert_eq(expected, sys.prefix)
        ''').run(appimage)

        # Test SSL (see issue #24).
        if version.major > 2:
            Script('''
from http import HTTPStatus
import urllib.request
with urllib.request.urlopen('https://wikipedia.org') as r:
    assert_eq(r.status, HTTPStatus.OK)
            ''').run(appimage)

        # Test pip installing to an extracted AppImage.
        r = system(f'{appdir}/AppRun -m pip install pip-install-test')
        assert('Successfully installed pip-install-test' in r)
        path = appdir / f'opt/python{version.flavoured()}/lib/python{version.flavoured()}/site-packages/pip_install_test'
        assert(path.exists())

        # Test tkinter (basic).
        tkinter = 'tkinter' if version.major > 2 else 'Tkinter'
        Script(f'''
import {tkinter} as tkinter
tkinter.Tk()
        ''').run(appimage)

        # Test venv.
        if version.major > 2:
            system(' && '.join((
                f'cd {tmpdir.name}',
                f'./{appimage.name} -m venv ENV',
                '. ENV/bin/activate',
            )))
            python = Path(f'{tmpdir.name}/ENV/bin/python')
            assert_eq(appimage.name, str(python.readlink()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = test.__doc__)
    parser.add_argument('appimage',
        help = 'path to appimage(s)',
        nargs = '+',
        type = lambda x: Path(x).absolute()
    )

    ARGS = parser.parse_args()
    test()
