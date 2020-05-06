# AppImage distributions of Python

_Ready to use AppImages of Python are available as GitHub [releases][RELEASES]._

## Quickstart

We provide relocatable Python runtimes as [AppImages][APPIMAGE]. These runtimes
are extracted from [manylinux][MANYLINUX] Docker images. The corresponding
images are available as GitHub [releases][RELEASES]. They are labeled according
to [wheels][WHEEL] compatibility tags. Our Python AppImages are updated
weekly.

Running Python from these [AppImages][APPIMAGE] is as simple as downloading a
single file and changing its mode to executable, e.g.  as:

```sh
wget https://github.com/niess/python-appimage/releases/download/\
python3.8/python3.8.2-cp38-cp38-manylinux1_x86_64.AppImage
chmod +x python3.8.2-cp38-cp38-manylinux1_x86_64.AppImage

./python3.8.2-cp38-cp38-manylinux1_x86_64.AppImage
```

This should start a Python 3.8 interactive session on _almost_ any Linux
provided that `fuse` is available. Note that on WSL1 since `fuse` is not
supported you will need to extract the AppImage as explained hereafter.

The workflow described previously is enough if you only need vanilla Python with
its standard library.  However, if you plan to install extra packages we
recommend extracting the AppImage, e.g. as:

```sh
./python3.8.2-cp38-cp38-manylinux1_x86_64.AppImage --appimage-extract
mv squashfs-root python3.8
rm -f python3.8.2-cp38-cp38-manylinux1_x86_64.AppImage

export PATH="$(pwd)/python3.8/usr/bin:$PATH"
```

Then, extra packages can be installed to the extracted AppDir using `pip`. For
example upgrading pip can be done as:

```sh
pip install --upgrade pip
```

## For applications developers

Python [AppImages][APPIMAGE] are built using the `python_appimage` Python
package. You can get it from [GitHub][GITHUB] or [PyPI][PYPI]. Examples of usage
can be found by browsing GitHub [workflows][WORKFLOWS].

The `python_appimage` package also allows to build basic Python apps from an
existing Python AppImage and a recipe folder. The recipe folder contains the
app metadata, a Python requirements file and an entry point script. Examples of
recipes can be found on GitHub in the [applications][APPLICATIONS] folder.

Alternatively, you can also manualy extract one of the Python [AppImages][APPIMAGE]
as explained above and directly modify the content, e.g. `pip install` your custom
packages. Then, simply rebuild the AppImage using your favourite tool, e.g.
[appimagetool][APPIMAGETOOL], [linuxdeploy][LINUXDEPLOY] or `python-appimage`.

## Make releases with AppImage in GitHub release assets with [Rever](https://regro.github.io/rever-docs/)

We recommend to test this process in safe place. The best way is to fork or copy the repository you're working on
to the distinct GitHub repository.

How to release AppImages with release your app on GitHub:

1. You have PyPi package with `setup.py` file and `pip install -U .` works perfect. 

2. You have AppImage description files like in 
[applications/xonsh](https://github.com/niess/python-appimage/tree/master/applications/xonsh) directory. 
And your AppImage can be build with:
```
python -m python_appimage build app ./path/to/package
```

3. Install [rever](https://regro.github.io/rever-docs/):
```
pip install -U rever
```

4. Create `appimage` directory near `setup.py` with AppImage description files 
and rename the `appimage/requirements.txt` to `appimage/pre-requirements.txt`. In release process your package directory 
will be added to `pre-requiriments.txt` and created `requirements.txt`.  

5. Create `rever.xsh` file near `setup.py`: 
```
$ACTIVITIES = ['tag', 'push_tag', 'appimage', 'ghrelease']

$GITHUB_ORG = 'anki-code'
$PROJECT = $GITHUB_REPO = 'mypackage'

$TAG_REMOTE = 'git@github.com:anki-code/mypackage.git'
$TAG_TARGET = 'master'
$PUSH_TAG_PROTOCOL='ssh'

# The name of your AppImage will be `<Name from .desktop-file>-<system>.AppImage` (`xonsh-x86_64.AppImage` for example).
$GHRELEASE_ASSETS = ['mypackage-x86_64.AppImage']
```
 
6. Run check and make release. In this example we have 4 steps: `tag`, `push_tag`, `appimage`, `ghrelease`. This means that rever will create `0.0.1` tag, 
push it to the remote, then build AppImage and create GitHub release:
```
rever check
rever 0.0.1
```  

7. Check the GitHub release page for AppImage assets

## Projects using [python-appimage][PYTHON_APPIMAGE]
* [grand/python](https://github.com/grand-mother/python) - Contained, portable
  and modern python for [GRAND][GRAND] running from an AppImage
* [xxh](https://github.com/xxh/xxh) - Bring your favorite shell wherever you go
  through the ssh 
* [xonsh](https://github.com/xonsh/xonsh) - Python-powered, cross-platform, Unix-gazing 
  shell language and command prompt
* [rever](https://github.com/regro/rever) - cross-platform software release tool.


[APPIMAGE]: https://appimage.org
[APPIMAGETOOL]: https://appimage.github.io/appimagetool
[APPLICATIONS]: https://github.com/niess/python-appimage/tree/master/applications
[GITHUB]: https://github.com/niess/python-appimage
[LINUXDEPLOY]: https://github.com/linuxdeploy/linuxdeploy
[MANYLINUX]: https://github.com/pypa/manylinux
[PYPI]: https://pypi.org/project/python-appimage
[RELEASES]: https://github.com/niess/python-appimage/releases
[WHEEL]: https://pythonwheels.com
[WORKFLOWS]: https://github.com/niess/python-appimage/tree/master/.github/workflows
[GRAND]: http://grand.cnrs.fr
[PYTHON_APPIMAGE]: https://github.com/niess/python-appimage