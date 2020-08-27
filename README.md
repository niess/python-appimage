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

## Projects using [python-appimage][PYTHON_APPIMAGE]
* [grand/python](https://github.com/grand-mother/python) - Contained, portable
  and modern python for [GRAND][GRAND] running from an AppImage
* [xxh](https://github.com/xxh/xxh) - Bring your favorite shell wherever you go
  through the ssh 
* [xonsh](https://github.com/xonsh/xonsh) - Python-powered, cross-platform, Unix-gazing 
  shell language and command prompt
* [rever](https://github.com/regro/rever) - Cross-platform software release tool.


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
