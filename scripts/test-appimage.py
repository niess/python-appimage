#! /usr/bin/env python3
import argparse
from enum import auto, Enum
import inspect
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import FunctionType
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


class Status(Enum):
    '''Test exit status'''
    FAILED = auto()
    SKIPPED = auto()
    SUCCESS = auto()

    def __str__(self):
        return self.name


def system(cmd):
    '''Run a system command'''

    r = subprocess.run(cmd, capture_output=True, shell=True)

    if r.returncode != 0:
        raise ValueError(r.stderr.decode())
    else:
        return r.stdout.decode()


class TestContext:
    '''Context for testing an image'''

    def __init__(self, appimage):
        self.appimage = appimage

        # Guess python version from appimage name.
        version, _, abi, *_ = appimage.name.split('-', 3)
        version = version[6:]
        if abi.endswith('t'):
            version += '-nogil'
        self.version = PythonVersion.from_str(version)

        # Get some specific AppImage env variables.
        self.env = eval(Script('''
import os
appdir = os.environ['APPDIR']
env = {}
for var in ('SSL_CERT_FILE', 'TCL_LIBRARY', 'TK_LIBRARY', 'TKPATH'):
    try:
        env[var] = os.environ[var].replace(appdir, '$APPDIR')
    except KeyError:
        pass
print(env)
        ''').run(appimage))

        # Extract the AppImage.
        tmpdir = tempfile.TemporaryDirectory()
        dst = Path(tmpdir.name) / appimage.name
        shutil.copy(appimage, dst)
        system(f'cd {tmpdir.name} && ./{appimage.name} --appimage-extract')
        self.appdir = Path(tmpdir.name) / 'squashfs-root'
        self.tmpdir = tmpdir

    def list_content(self, path=None):
        '''List the content of an extracted directory'''

        path = self.appdir if path is None else self.appdir / path
        return sorted(os.listdir(path))

    def run(self):
        '''Run all tests'''

        tests = []
        for key, value in self.__class__.__dict__.items():
            if isinstance(value, FunctionType):
                if key.startswith('test_'):
                    tests.append(value)

        n = len(tests)
        m = max(len(test.__doc__) for test in tests)
        for i, test in enumerate(tests):
            sys.stdout.write(
                f'[ {self.appimage.name} | {i + 1:2}/{n} ] {test.__doc__:{m}}'
            )
            sys.stdout.flush()
            try:
                status = test(self)
            except Exception as e:
                status = Status.FAILED
                sys.stdout.write(
                    f'  ->  {status} ({test.__name__}){os.linesep}')
                sys.stdout.flush()
                raise e
            else:
                sys.stdout.write(f'  ->  {status}{os.linesep}')
                sys.stdout.flush()


    def test_root_content(self):
        '''Check the appimage root content'''

        content = self.list_content()
        expected = ['.DirIcon', 'AppRun', 'opt', 'python.png',
                    f'python{self.version.long()}.desktop', 'usr']
        assert_eq(expected, content)
        return Status.SUCCESS

    def test_python_content(self):
        '''Check the appimage python content'''

        prefix = f'opt/python{self.version.flavoured()}'
        content = self.list_content(prefix)
        assert_eq(['bin', 'include', 'lib'], content)
        content = self.list_content(f'{prefix}/bin')
        assert_eq(
            [f'pip{self.version.short()}', f'python{self.version.flavoured()}'],
            content
        )
        content = self.list_content(f'{prefix}/include')
        if (self.version.major == 3) and (self.version.minor <= 7):
            expected = [f'python{self.version.short()}m']
        else:
            expected = [f'python{self.version.flavoured()}']
        assert_eq(expected, content)
        content = self.list_content(f'{prefix}/lib')
        assert_eq([f'python{self.version.flavoured()}'], content)
        return Status.SUCCESS

    def test_system_content(self):
        '''Check the appimage system content'''

        content = self.list_content('usr')
        assert_eq(['bin', 'lib', 'share'], content)
        content = self.list_content('usr/bin')
        expected = [
            'pip', f'pip{self.version.major}', f'pip{self.version.short()}',
            'python', f'python{self.version.major}',
            f'python{self.version.short()}'
        ]
        assert_eq(expected, content)
        return Status.SUCCESS

    def test_tcltk_bundling(self):
        '''Check Tcl/Tk bundling'''

        if 'TK_LIBRARY' not in self.env:
            return Status.SKIPPED
        else:
            for var in ('TCL_LIBRARY', 'TK_LIBRARY', 'TKPATH'):
                path = Path(self.env[var].replace('$APPDIR', str(self.appdir)))
                assert path.exists()
            return Status.SUCCESS

    def test_ssl_bundling(self):
        '''Check SSL certs bundling'''

        var = 'SSL_CERT_FILE'
        path = Path(self.env[var].replace('$APPDIR', str(self.appdir)))
        assert path.exists()
        return Status.SUCCESS

    def test_bin_symlinks(self):
        '''Check /usr/bin symlinks'''

        assert_eq(
            (self.appdir /
             f'opt/python{self.version.flavoured()}/bin/pip{self.version.short()}'),
            (self.appdir / f'usr/bin/pip{self.version.short()}').resolve()
        )
        assert_eq(
            f'pip{self.version.short()}',
            str((self.appdir / f'usr/bin/pip{self.version.major}').readlink())
        )
        assert_eq(
            f'pip{self.version.major}',
            str((self.appdir / 'usr/bin/pip').readlink())
        )
        assert_eq(
            f'python{self.version.short()}',
            str((self.appdir / f'usr/bin/python{self.version.major}').readlink())
        )
        assert_eq(
            f'python{self.version.major}',
            str((self.appdir / 'usr/bin/python').readlink())
        )
        return Status.SUCCESS

    def test_appimage_hook(self):
        '''Test the appimage hook'''

        Script(f'''
import os
assert_eq(os.environ['APPIMAGE_COMMAND'], '{self.appimage}')

import sys
assert_eq('{self.appimage}', sys.executable)
assert_eq('{self.appimage}', sys._base_executable)
        ''').run(self.appimage)
        return Status.SUCCESS

    def test_python_prefix(self):
        '''Test the python prefix'''

        Script(f'''
import os
import sys
expected = os.environ["APPDIR"] + '/opt/python{self.version.flavoured()}'
assert_eq(expected, sys.prefix)
        ''').run(self.appimage)
        return Status.SUCCESS

    def test_ssl_request(self):
        '''Test SSL request (see issue #24)'''

        if self.version.major == 2:
            return Status.SKIPPED
        else:
            Script('''
from http import HTTPStatus
import urllib.request
with urllib.request.urlopen('https://wikipedia.org') as r:
    assert_eq(r.status, HTTPStatus.OK)
            ''').run(self.appimage)
        return Status.SUCCESS

    def test_pip_install(self):
        '''Test pip installing to an extracted AppImage'''

        r = system(f'{self.appdir}/AppRun -m pip install pip-install-test')
        assert('Successfully installed pip-install-test' in r)
        path = self.appdir / f'opt/python{self.version.flavoured()}/lib/python{self.version.flavoured()}/site-packages/pip_install_test'
        assert(path.exists())
        return Status.SUCCESS

    def test_tkinter_usage(self):
        '''Test basic tkinter usage'''

        try:
            os.environ['DISPLAY']
            self.env['TK_LIBRARY']
        except KeyError:
            return Status.SKIPPED
        else:
            tkinter = 'tkinter' if self.version.major > 2 else 'Tkinter'
            Script(f'''
    import {tkinter} as tkinter
    tkinter.Tk()
            ''').run(self.appimage)
            return Status.SUCCESS

    def test_venv_usage(self):
        '''Test venv creation'''

        if self.version.major == 2:
            return Status.SKIPPED
        else:
            system(' && '.join((
                f'cd {self.tmpdir.name}',
                f'./{self.appimage.name} -m venv ENV',
                '. ENV/bin/activate',
            )))
            python = Path(f'{self.tmpdir.name}/ENV/bin/python')
            assert_eq(self.appimage.name, str(python.readlink()))
            return Status.SUCCESS


def test():
    '''Test Python AppImage(s)'''

    for appimage in ARGS.appimage:
        context = TestContext(appimage)
        context.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = test.__doc__)
    parser.add_argument('appimage',
        help = 'path to appimage(s)',
        nargs = '+',
        type = lambda x: Path(x).absolute()
    )

    ARGS = parser.parse_args()
    test()
