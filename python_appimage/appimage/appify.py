from dataclasses import dataclass
import glob
import os
from typing import Optional

from ..utils.deps import PREFIX
from ..utils.fs import copy_file, make_tree, remove_file
from ..utils.log import log
from ..utils.template import copy_template, load_template


@dataclass(frozen=True)
class Appifier:
    '''Helper class for bundling AppImage specific files'''

    '''Path to AppDir root.'''
    appdir: str

    '''Path to AppDir executables.'''
    appdir_bin: str

    '''Path to Python executables.'''
    python_bin: str

    '''Path to Python site-packages.'''
    python_pkg: str

    '''Tcl/Tk version.'''
    tk_version: str

    '''Python version.'''
    version: 'PythonVersion'

    '''Path to SSL certification file.'''
    cert_src: Optional[str]=None

    def appify(self):
        '''Bundle Appimage specific files'''

        python_x_y = f'python{self.version.short()}'
        pip_x_y = f'pip{self.version.short()}'

        # Add a runtime patch for sys.executable, before site.main() execution
        log('PATCH', f'{python_x_y} sys.executable')
        set_executable_patch(
            self.version.short(),
            self.python_pkg,
            PREFIX + '/data/_initappimage.py'
        )

        # Set a hook for cleaning sys.path, after site.main() execution
        log('HOOK', f'{python_x_y} sys.path')

        sitepkgs = self.python_pkg + '/site-packages'
        make_tree(sitepkgs)
        copy_file(PREFIX + '/data/sitecustomize.py', sitepkgs)

        # Symlink SSL certificates
        # (see https://github.com/niess/python-appimage/issues/24)
        cert_file = '/opt/_internal/certs.pem'
        cert_dst = f'{self.appdir}{cert_file}'
        if self.cert_src is not None:
            if os.path.exists(self.cert_src):
                if not os.path.exists(cert_dst):
                    dirname, basename = os.path.split(cert_dst)
                    relpath = os.path.relpath(self.cert_src, dirname)
                    make_tree(dirname)
                    os.symlink(relpath, cert_dst)
                    log('INSTALL', basename)
        if not os.path.exists(cert_dst):
            cert_file = None

        # Bundle the python wrapper
        wrapper = f'{self.appdir_bin}/{python_x_y}'
        if not os.path.exists(wrapper):
            log('INSTALL', f'{python_x_y} wrapper')
            entrypoint_path = PREFIX + '/data/entrypoint.sh'
            entrypoint = load_template(
                entrypoint_path,
                python=f'python{self.version.flavoured()}'
            )
            dictionary = {
                'entrypoint': entrypoint,
                'shebang': '#! /bin/bash',
                'tcltk-env': tcltk_env_string(self.python_pkg, self.tk_version)
            }
            if cert_file:
                dictionary['cert-file'] = cert_file_env_string(cert_file)
            else:
                dictionary['cert-file'] = ''

            _copy_template('python-wrapper.sh', wrapper, **dictionary)

        # Set or update symlinks to python and pip.
        pip_target = f'{self.python_bin}/{pip_x_y}'
        if os.path.exists(pip_target):
            relpath = os.path.relpath(pip_target, self.appdir_bin)
            os.symlink(relpath, f'{self.appdir_bin}/{pip_x_y}')

        pythons = glob.glob(self.appdir_bin + '/python?.*')
        versions = [os.path.basename(python)[6:] for python in pythons]
        latest2, latest3 = '0.0', '0.0'
        for version in versions:
            if version.startswith('2') and version >= latest2:
                latest2 = version
            elif version.startswith('3') and version >= latest3:
                latest3 = version
        if latest2 == self.version.short():
            python2 = self.appdir_bin + '/python2'
            remove_file(python2)
            os.symlink(python_x_y, python2)
            has_pip = os.path.exists(self.appdir_bin + '/' + pip_x_y)
            if has_pip:
                pip2 = self.appdir_bin + '/pip2'
                remove_file(pip2)
                os.symlink(pip_x_y, pip2)
            if latest3 == '0.0':
                log('SYMLINK', 'python, python2 to ' + python_x_y)
                python = self.appdir_bin + '/python'
                remove_file(python)
                os.symlink('python2', python)
                if has_pip:
                    log('SYMLINK', 'pip, pip2 to ' + pip_x_y)
                    pip = self.appdir_bin + '/pip'
                    remove_file(pip)
                    os.symlink('pip2', pip)
            else:
                log('SYMLINK', 'python2 to ' + python_x_y)
                if has_pip:
                    log('SYMLINK', 'pip2 to ' + pip_x_y)
        elif latest3 == self.version.short():
            log('SYMLINK', 'python, python3 to ' + python_x_y)
            python3 = self.appdir_bin + '/python3'
            remove_file(python3)
            os.symlink(python_x_y, python3)
            python = self.appdir_bin + '/python'
            remove_file(python)
            os.symlink('python3', python)
            if os.path.exists(self.appdir_bin + '/' + pip_x_y):
                log('SYMLINK', 'pip, pip3 to ' + pip_x_y)
                pip3 = self.appdir_bin + '/pip3'
                remove_file(pip3)
                os.symlink(pip_x_y, pip3)
                pip = self.appdir_bin + '/pip'
                remove_file(pip)
                os.symlink('pip3', pip)

        # Bundle the entry point
        apprun = f'{self.appdir}/AppRun'
        if not os.path.exists(apprun):
            log('INSTALL', 'AppRun')

            relpath = os.path.relpath(wrapper, self.appdir)
            os.symlink(relpath, apprun)

        # Bundle the desktop file
        desktop_name = f'python{self.version.long()}.desktop'
        desktop = os.path.join(self.appdir, desktop_name)
        if not os.path.exists(desktop):
            log('INSTALL', desktop_name)
            apps = 'usr/share/applications'
            appfile = f'{self.appdir}/{apps}/{desktop_name}'
            if not os.path.exists(appfile):
                make_tree(os.path.join(self.appdir, apps))
                _copy_template('python.desktop', appfile,
                               version=self.version.short(),
                               fullversion=self.version.long())
            os.symlink(os.path.join(apps, desktop_name), desktop)

        # Bundle icons
        icons = 'usr/share/icons/hicolor/256x256/apps'
        icon = os.path.join(self.appdir, 'python.png')
        if not os.path.exists(icon):
            log('INSTALL', 'python.png')
            make_tree(os.path.join(self.appdir, icons))
            copy_file(PREFIX + '/data/python.png',
                      os.path.join(self.appdir, icons, 'python.png'))
            os.symlink(os.path.join(icons, 'python.png'), icon)

        diricon = os.path.join(self.appdir, '.DirIcon')
        if not os.path.exists(diricon):
            os.symlink('python.png', diricon)

        # Bundle metadata
        meta_name = f'python{self.version.long()}.appdata.xml'
        meta_dir = os.path.join(self.appdir, 'usr/share/metainfo')
        meta_file = os.path.join(meta_dir, meta_name)
        if not os.path.exists(meta_file):
            log('INSTALL', meta_name)
            make_tree(meta_dir)
            _copy_template(
                'python.appdata.xml',
                meta_file,
                version = self.version.short(),
                fullversion = self.version.long()
            )


def cert_file_env_string(cert_file):
    '''Environment for using a bundled certificate
    '''
    if cert_file:
        return '''
# Export SSL certificate
export SSL_CERT_FILE="${{APPDIR}}{cert_file:}"'''.format(
    cert_file=cert_file)
    else:
        return ''


def _copy_template(name, destination, **kwargs):
    path = os.path.join(PREFIX, 'data', name)
    copy_template(path, destination, **kwargs)


def tcltk_env_string(python_pkg, tk_version):
    '''Environment for using AppImage's TCl/Tk
    '''

    if tk_version:
        return '''
# Export TCl/Tk
export TCL_LIBRARY="${{APPDIR}}/usr/share/tcltk/tcl{tk_version:}"
export TK_LIBRARY="${{APPDIR}}/usr/share/tcltk/tk{tk_version:}"
export TKPATH="${{TK_LIBRARY}}"'''.format(
    tk_version=tk_version)
    else:
        return ''


def set_executable_patch(version, pkgpath, patch):
    '''Set a runtime patch for sys.executable name
    '''

    # This patch needs to be executed before site.main() is called. A natural
    # option is to apply it directy to the site module. But, starting with
    # Python 3.11, the site module is frozen within Python executable. Then,
    # doing so would require to recompile Python. Thus, starting with 3.11 we
    # instead apply the patch to the encodings package. Indeed, the latter is
    # loaded before the site module, and it is not frozen (as for now).
    major, minor = [int(v) for v in version.split('.')]
    if (major >= 3) and (minor >= 11):
        path = os.path.join(pkgpath, 'encodings', '__init__.py')
    else:
        path = os.path.join(pkgpath, 'site.py')

    with open(path) as f:
        source = f.read()

    if '_initappimage' in source: return

    lines = source.split(os.linesep)

    if path.endswith('site.py'):
        # Insert the patch before the main function
        for i, line in enumerate(lines):
            if line.startswith('def main('): break
    else:
        # Append the patch at end of file
        i = len(lines)

    with open(patch) as f:
        patch = f.read()

    lines.insert(i, patch)
    lines.insert(i + 1, '')

    source = os.linesep.join(lines)
    with open(path, 'w') as f:
        f.write(source)
