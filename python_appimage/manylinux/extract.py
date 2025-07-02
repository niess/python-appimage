import atexit
from dataclasses import dataclass, field
from distutils.version import LooseVersion
import glob
import json
import os
import re
from pathlib import Path
import shutil
import stat
import subprocess
from typing import Dict, List, Optional

from .config import Arch, PythonImpl, PythonVersion
from ..appimage import Appifier
from ..utils.deps import ensure_excludelist, ensure_patchelf, EXCLUDELIST, \
                         PATCHELF
from ..utils.log import debug, log


@dataclass(frozen=True)
class PythonExtractor:
    '''Python extractor from an extracted Manylinux image.'''

    arch: Arch
    '''Target architecture'''

    prefix: Path
    '''Target image path'''

    tag: str
    '''Python binary tag'''


    excludelist: Optional[Path] = None
    '''Exclude list for shared libraries.'''

    patchelf: Optional[Path] = None
    '''Patchelf executable.'''


    excluded: List[str] = field(init=False)
    '''Excluded shared libraries.'''

    impl: PythonImpl = field(init=False)
    '''Python implementation'''

    library_path: List[str] = field(init=False)
    '''Search paths for libraries (LD_LIBRARY_PATH)'''

    python_prefix: Path = field(init=False)
    '''Python installation prefix'''

    version: PythonVersion = field(init=False)
    '''Python version'''


    def __post_init__(self):
        # Locate Python installation.
        link = os.readlink(self.prefix / f'opt/python/{self.tag}')
        if not link.startswith('/'):
            raise NotImplementedError()
        object.__setattr__(self, 'python_prefix', self.prefix / link[1:])

        # Parse implementation and version.
        head, tail = Path(link).name.split('-', 1)
        if head == 'cpython':
            impl = PythonImpl.CPYTHON
            version = PythonVersion.from_str(tail)
        else:
            raise NotImplementedError()
        object.__setattr__(self, 'impl', impl)
        object.__setattr__(self, 'version', version)

        # Set libraries search path.
        paths = []
        if self.arch in (Arch.AARCH64, Arch.X86_64):
            paths.append(self.prefix / 'lib64')
            paths.append(self.prefix / 'usr/lib64')
            if self.arch == Arch.X86_64:
                paths.append(self.prefix / 'lib/x86_64-linux-gnu')
                paths.append(self.prefix / 'usr/lib/x86_64-linux-gnu')
            else:
                paths.append(self.prefix / 'lib/aarch64-linux-gnu')
                paths.append(self.prefix / 'usr/lib/aarch64-linux-gnu')
        elif self.arch == Arch.I686:
            paths.append(self.prefix / 'lib')
            paths.append(self.prefix / 'usr/lib')
            paths.append(self.prefix / 'lib/i386-linux-gnu')
            paths.append(self.prefix / 'usr/lib/i386-linux-gnu')
        else:
            raise NotImplementedError()
        paths.append(self.prefix / 'usr/local/lib')

        patterns = (
            'curl-*',
            'mpdecimal-*',
            'openssl-*',
            'sqlite*',
        )
        for pattern in patterns:
            pattern = str(self.prefix / f'opt/_internal/{pattern}/lib')
            for match in glob.glob(pattern):
                paths.append(Path(match))

        object.__setattr__(self, 'library_path', paths)

        # Set excluded libraries.
        if self.excludelist:
            excludelist = Path(self.excludelist)
        else:
            ensure_excludelist()
            excludelist = Path(EXCLUDELIST)
        excluded = set()
        with excludelist.open() as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    excluded.add(line)
        excluded.add('ld-linux-aarch64.so.1')  # patch for aarch64.
        object.__setattr__(self, 'excluded', excluded)

        # Set patchelf, if not provided.
        if self.patchelf is None:
            ensure_patchelf()
            object.__setattr__(self, 'patchelf', PATCHELF)
        else:
            assert(self.patchelf.exists())


    def extract(
        self,
        destination: Path,
        *,
        appify: Optional[bool]=False,
        python_prefix: Optional[str]=None,
        system_prefix: Optional[str]=None,
        ):
        '''Extract Python runtime.'''

        python = f'python{self.version.short()}'
        flavoured_python = f'python{self.version.flavoured()}'
        runtime = f'bin/{flavoured_python}'
        packages = f'lib/{flavoured_python}'
        pip = f'bin/pip{self.version.short()}'

        if python_prefix is None:
            python_prefix = f'opt/{flavoured_python}'

        if system_prefix is None:
            system_prefix = 'usr'

        python_dest = destination / python_prefix
        system_dest = destination / system_prefix

        # Locate include files.
        include = glob.glob(str(self.python_prefix / 'include/*'))
        if include:
            include = Path(include[0]).name
            include = f'include/{include}'
        else:
            raise NotImplementedError()

        # Clone Python runtime.
        log('CLONE',
            f'{python} from {self.python_prefix.relative_to(self.prefix)}')
        (python_dest / 'bin').mkdir(exist_ok=True, parents=True)
        shutil.copy(self.python_prefix / runtime, python_dest / runtime)

        # Clone pip wrapper.
        with open(self.python_prefix / pip) as f:
            f.readline() # Skip shebang.
            body = f.read()

        with open(python_dest / pip, 'w') as f:
            f.write('#! /bin/sh\n')
            f.write(' '.join((
                '"exec"',
                f'"$(dirname $(readlink -f ${0}))/{flavoured_python}"',
                '"$0"',
                '"$@"\n'
            )))
            f.write(body)
        shutil.copymode(self.python_prefix / pip, python_dest / pip)

        # Clone Python packages.
        for folder in (packages, include):
            shutil.copytree(self.python_prefix / folder, python_dest / folder,
                            symlinks=True, dirs_exist_ok=True)

        # Remove some clutters.
        log('PRUNE', '%s packages', python)
        shutil.rmtree(python_dest / packages / 'test', ignore_errors=True)
        for root, dirs, files in os.walk(python_dest / packages):
            root = Path(root)
            for d in dirs:
                if d == '__pycache__':
                    shutil.rmtree(root / d, ignore_errors=True)
            for f in files:
                if f.endswith('.pyc'):
                    (root / f).unlink()

        # Map binary dependencies.
        libs = self.ldd(self.python_prefix / f'bin/{flavoured_python}')
        path = Path(self.python_prefix / f'{packages}/lib-dynload')
        for module in glob.glob(str(path / "*.so")):
            l = self.ldd(module)
            libs.update(l)

        # Copy and patch binary dependencies.
        libdir = system_dest / 'lib'
        libdir.mkdir(exist_ok=True, parents=True)

        for (name, src) in libs.items():
            dst = libdir / name
            shutil.copy(src, dst, follow_symlinks=True)
            # Some libraries are read-only, which prevents overriding the
            # destination directory. Below, we change the permission of
            # destination files to read-write (for the owner).
            mode = dst.stat().st_mode
            if not (mode & stat.S_IWUSR):
                mode = mode | stat.S_IWUSR
                dst.chmod(mode)

            self.set_rpath(dst, '$ORIGIN')

        # Patch RPATHs of binary modules.
        log('LINK', '%s C-extensions', python)
        path = Path(python_dest / f'{packages}/lib-dynload')
        for module in glob.glob(str(path / "*.so")):
            src = Path(module)
            dst = os.path.relpath(libdir, src.parent)
            self.set_rpath(src, f'$ORIGIN/{dst}')

        # Patch RPATHs of Python runtime.
        src = python_dest / runtime
        dst = os.path.relpath(libdir, src.parent)
        self.set_rpath(src, f'$ORIGIN/{dst}')

        # Copy SSL certificates (i.e. clone certifi).
        certs = self.prefix / 'opt/_internal/certs.pem'
        if certs.is_symlink():
            dst = self.prefix / str(certs.readlink())[1:]
            certifi = dst.parent
            assert(certifi.name == 'certifi')
            site_packages = certifi.parent
            assert(site_packages.name == 'site-packages')
            log('INSTALL', certifi.name)

            matches = [
                Path(src) for src in glob.glob(str(site_packages / 'certifi*'))
            ]
            matches = sorted(matches, key=lambda src: src.name)
            cert_src = None
            for src in matches:
                dst = python_dest / f'{packages}/site-packages/{src.name}'
                if not dst.exists():
                    shutil.copytree(src, dst, symlinks=True)
                if cert_src is None:
                    cacert_pem = dst / 'cacert.pem'
                    if cacert_pem.exists():
                        cert_src = cacert_pem
            assert(cert_src is not None)
        else:
            raise NotImplementedError()

        # Copy Tcl & Tk data.
        tx_version = []
        for match in glob.glob(str(system_dest / 'lib/libtk*')):
            path = system_dest / f'lib/{match}'
            tx_version.append(LooseVersion(path.name[5:8]))

        if tx_version:
            tx_version.sort()
            tx_version = tx_version[-1]

            for location in ('usr/local/lib', 'usr/share', 'usr/share/tcltk'):
                tcltk_src = self.prefix / location
                path = tcltk_src / f'tk{tx_version}'
                if path.exists() and path.is_dir():
                    break
            else:
                raise ValueError(f'could not locate Tcl/Tk{tx_version}')

            log('INSTALL', f'Tcl/Tk{tx_version}')
            tcltk_dir = Path(system_dest / 'share/tcltk')
            tcltk_dir.mkdir(exist_ok=True, parents=True)

            for tx in ('tcl', 'tk'):
                name = f'{tx}{tx_version}'
                src = tcltk_src / name
                dst = tcltk_dir / name
                shutil.copytree(src, dst, symlinks=True, dirs_exist_ok=True)

        if appify:
            appifier = Appifier(
                appdir = str(destination),
                appdir_bin = str(system_dest / 'bin'),
                python_bin = str(python_dest / 'bin'),
                python_pkg = str(python_dest / packages),
                version = self.version,
                tk_version = tx_version,
                cert_src = cert_src
            )
            appifier.appify()


    def ldd(self, target: Path) -> Dict[str, Path]:
        '''Cross-platform implementation of ldd, using readelf.'''

        pattern = re.compile(r'[(]NEEDED[)]\s+Shared library:\s+\[([^\]]+)\]')
        dependencies = dict()

        def recurse(target: Path):
            result = subprocess.run(f'readelf -d {target}', shell=True,
                                    check=True, capture_output=True)
            stdout = result.stdout.decode()
            matches = pattern.findall(stdout)

            for match in matches:
                if (match not in dependencies) and (match not in self.excluded):
                    path = self.locate_library(match)
                    dependencies[match] = path
                    recurse(path)

        recurse(target)
        return dependencies


    def locate_library(self, name: str) -> Path:
        '''Locate a library given its qualified name.'''

        for dirname in self.library_path:
            path = dirname / name
            if path.exists():
                return path
        else:
            raise FileNotFoundError(name)


    def set_rpath(self, target, rpath):
        cmd = f'{self.patchelf} --print-rpath {target}'
        result = subprocess.run(cmd, shell=True, check=True,
                                capture_output=True)
        current_rpath = result.stdout.decode().strip()
        if current_rpath != rpath:
            cmd = f"{self.patchelf} --set-rpath '{rpath}' {target}"
            subprocess.run(cmd, shell=True, check=True, capture_output=True)


@dataclass(frozen=True)
class ImageExtractor:
    '''Manylinux image extractor from layers.'''

    prefix: Path
    '''Manylinux image prefix.'''

    tag: Optional[str] = 'latest'
    '''Manylinux image tag.'''


    def default_destination(self):
        return self.prefix / f'extracted/{self.tag}'


    def extract(self, destination: Optional[Path]=None, *, clean=False):
        '''Extract Manylinux image.'''

        if destination is None:
            destination = self.default_destination()

        if clean:
            def clean(destination):
                shutil.rmtree(destination, ignore_errors=True)
            atexit.register(clean, destination)

        log('EXTRACT', f'{self.prefix.name}:{self.tag}')

        with open(self.prefix / f'tags/{self.tag}.json') as f:
            meta = json.load(f)
        layers = meta['layers']

        extracted = []
        extracted_file = destination / '.extracted'
        if destination.exists():
            clean_destination = True
            if extracted_file.exists():
                with extracted_file.open() as f:
                    extracted = f.read().split(os.linesep)[:-1]

                for a, b in zip(layers, extracted):
                    if a != b:
                        break
                else:
                    clean_destination = False

            if clean_destination:
                shutil.rmtree(destination, ignore_errors=True)

        for i, layer in enumerate(layers):
            try:
                if layer == extracted[i]:
                    continue
            except IndexError:
                pass

            debug('EXTRACT', f'{layer}.tar.gz')
            filename = self.prefix / f'layers/{layer}.tar.gz'
            cmd = ''.join((
                 f'trap \'chmod u+rw -R {destination}\' EXIT ; ',
                 f'mkdir -p {destination} && ',
                 f'tar -xzf {filename} --exclude=dev -C {destination} && ',
                 f'echo \'{layer}\' >> {extracted_file}'
            ))
            r = subprocess.run(f'/bin/bash -c "{cmd}"', shell=True,
                               capture_output=True)
            if r.returncode != 0:
                raise ValueError(r.stderr.decode())
