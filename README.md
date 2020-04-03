# AppImage distributions of Python

_Ready to use AppImages of Python are available as GitHub [releases][RELEASES]._

## Quickstart

Our AppImages provide relocatable Python runtimes. Installation is as simple as
downloading a single file and changing its mode to executable, e.g.  as:

```sh
wget https://github.com/niess/python-appimage/releases/download/\
python3.8/python3.8.2-cp38-cp38-manylinux1_x86_64.AppImage
chmod +x python3.8.2-cp38-cp38-manylinux1_x86_64.AppImage

./python3.8.2-cp38-cp38-manylinux1_x86_64.AppImage
```

This should run Python 3.8 on _almost_ any Linux provided that `fuse` is
available. Note that on WSL1 since `fuse` is not supported you will need to
extract the AppImage as explained hereafter.

The installation mode described previously is enough if you only need vanilla
Python with its standard library.  However, if you plan to install extra
packages we recommmed extracting the AppImage, e.g. as:

```sh
./python3.8.2-cp38-cp38-manylinux1_x86_64.AppImage --appimage-extract
mv squashfs-root python3.8.2-cp38-cp38-manylinux1_x86_64.AppDir
rm -f python3.8.2-cp38-cp38-manylinux1_x86_64.AppImage

ln -s python3.8.2-cp38-cp38-manylinux1_x86_64.AppDir/AppRun python3.8
```

Then, extra packages can be installed to the extracted AppDir using `pip`. For
example updating pip can be done as:

```sh
./python3.8 -m pip install -U pip
```


[RELEASES]: https://github.com/niess/python-appimage/releases
