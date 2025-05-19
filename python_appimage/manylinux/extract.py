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
from typing import Dict, List, NamedTuple, Optional, Union

from .config import Arch, PythonImpl, PythonVersion
from ..utils.deps import ensure_excludelist, EXCLUDELIST
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
        elif self.arch == Arch.I686:
            paths.append(self.prefix / 'lib')
        else:
            raise NotImplementedError()
        paths.append(self.prefix / 'usr/local/lib')

        ssl = glob.glob(str(self.prefix / 'opt/_internal/openssl-*'))
        if ssl:
            paths.append(Path(ssl[0]) / 'lib')

        object.__setattr__(self, 'library_path', paths)

        # Set excluded libraries.
        if self.excludelist:
            excludelist = Path(self.excludelist)
        else:
            ensure_excludelist()
            excludelist = Path(EXCLUDELIST)
        excluded = []
        with excludelist.open() as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    excluded.append(line)
        object.__setattr__(self, 'excluded', excluded)

        # Set patchelf, if not provided.
        if self.patchelf is None:
            paths = (
                Path(__file__).parent / 'bin',
                Path.home() / '.local/bin'
            )
            for path in paths:
                patchelf = path / 'patchelf'
                if patchelf.exists():
                    break
            else:
                raise NotImplementedError()
            object.__setattr__(self, 'patchelf', patchelf)
        else:
            assert(self.patchelf.exists())


    def extract(self, destination):
        '''Extract Python runtime.'''

        python = f'python{self.version.short()}'
        runtime = f'bin/{python}'
        packages = f'lib/{python}'
        pip = f'bin/pip{self.version.short()}'

        # Locate include files.
        include = glob.glob(str(self.python_prefix / 'include/*'))
        if include:
            include = Path(include[0]).name
            include = f'include/{include}'
        else:
            raise NotImplementedError()

        # Clone Python runtime.
        (destination / 'bin').mkdir(exist_ok=True, parents=True)
        shutil.copy(self.python_prefix / runtime, destination / runtime)

        short = Path(destination / f'bin/python{self.version.major}')
        short.unlink(missing_ok=True)
        short.symlink_to(python)
        short = Path(destination / 'bin/python')
        short.unlink(missing_ok=True)
        short.symlink_to(f'python{self.version.major}')

        # Clone pip wrapper.
        with open(self.python_prefix / pip) as f:
            f.readline() # Skip shebang.
            body = f.read()

        with open(destination / pip, 'w') as f:
            f.write('#! /bin/sh\n')
            f.write(' '.join((
                '"exec"',
                f'"$(dirname $(readlink -f ${0}))/{python}"',
                '"$0"',
                '"$@"\n'
            )))
            f.write(body)
        shutil.copymode(self.python_prefix / pip, destination / pip)

        short = Path(destination / f'bin/pip{self.version.major}')
        short.unlink(missing_ok=True)
        short.symlink_to(f'pip{self.version.short()}')
        short = Path(destination / 'bin/pip')
        short.unlink(missing_ok=True)
        short.symlink_to(f'pip{self.version.major}')

        # Clone Python packages.
        for folder in (packages, include):
            shutil.copytree(self.python_prefix / folder, destination / folder,
                            symlinks=True, dirs_exist_ok=True)

        # Remove some clutters.
        shutil.rmtree(destination / packages / 'test', ignore_errors=True)
        for root, dirs, files in os.walk(destination / packages):
            root = Path(root)
            for d in dirs:
                if d == '__pycache__':
                    shutil.rmtree(root / d, ignore_errors=True)
            for f in files:
                if f.endswith('.pyc'):
                    (root / f).unlink()

        # Map binary dependencies.
        libs = self.ldd(self.python_prefix / f'bin/{python}')
        path = Path(self.python_prefix / f'{packages}/lib-dynload')
        for module in glob.glob(str(path / "*.so")):
            l = self.ldd(module)
            libs.update(l)

        # Copy and patch binary dependencies.
        libdir = destination / 'lib'
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
        path = Path(destination / f'{packages}/lib-dynload')
        for module in glob.glob(str(path / "*.so")):
            src = Path(module)
            dst = os.path.relpath(libdir, src.parent)
            self.set_rpath(src, f'$ORIGIN/{dst}')

        # Patch RPATHs of Python runtime.
        src = destination / runtime
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

            for src in glob.glob(str(site_packages / 'certifi*')):
                src = Path(src)
                dst = destination / f'{packages}/site-packages/{src.name}'
                if not dst.exists():
                    shutil.copytree(src, dst, symlinks=True)
        else:
            raise NotImplementedError()

        # Copy Tcl & Tk data.
        tcltk_src = self.prefix / 'usr/local/lib'
        tx_version = []
        for match in glob.glob(str(tcltk_src / 'tk*')):
            path = Path(match)
            if path.is_dir():
                tx_version.append(LooseVersion(path.name[2:]))
        tx_version.sort()
        tx_version = tx_version[-1]

        tcltk_dir = Path(destination / 'usr/share/tcltk')
        tcltk_dir.mkdir(exist_ok=True, parents=True)

        for tx in ('tcl', 'tk'):
            name = f'{tx}{tx_version}'
            src = tcltk_src / name
            dst = tcltk_dir / name
            shutil.copytree(src, dst, symlinks=True, dirs_exist_ok=True)


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
                    subs = recurse(path)

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


    def extract(self, destination: Path):
        '''Extract Manylinux image.'''

        with open(self.prefix / f'tags/{self.tag}.json') as f:
            meta = json.load(f)
        layers = meta['layers']

        for layer in layers:
            debug('EXTRACT', f'{layer}.tar.gz')

            filename = self.prefix / f'layers/{layer}.tar.gz'
            cmd = ' && '.join((
                 f'mkdir -p {destination}',
                 f'tar -xzf {filename} -C {destination}',
                 f'chmod u+rw -R {destination}'
            ))
            process = subprocess.run(cmd, shell=True, check=True,
                                     capture_output=True)
