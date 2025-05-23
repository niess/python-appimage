# AppImage distributions of Python

_Ready to use AppImages of Python are available as GitHub [releases][RELEASES]._


## Quickstart

We provide relocatable Python runtimes in the form of [AppImages][APPIMAGE] for
Linux systems. These runtimes are extracted from [Manylinux][MANYLINUX] Docker
images and are available as GitHub [releases][RELEASES]. Our Python AppImages
are updated weekly, on every Sunday.

Instructions for _installing_ and running _Python AppImages_ can be found on
[Read the Docs][READTHEDOCS].

The online documentation also describes the [`python-appimage`][PYPI] utility
for application developers. This utility can facilitate the development of
Python applications, provided you have an existing Python AppImage and a recipe
folder. [Examples][APPLICATIONS] of recipes are available on GitHub.


## Projects using [`python-appimage`][GITHUB]

* [grand/python](https://github.com/grand-mother/python) - Contained, portable
  and modern python for [GRAND][GRAND] running from an AppImage
* [rever](https://github.com/regro/rever) - Cross-platform software release tool.
* [ssh-mitm](https://github.com/ssh-mitm/ssh-mitm) - ssh mitm server for security audits
* [xonsh](https://github.com/xonsh/xonsh) - Python-powered, cross-platform, Unix-gazing
  shell language and command prompt
* [xxh](https://github.com/xxh/xxh) - Bring your favorite shell wherever you go
  through the ssh


## License

The [`python-appimage`][PYPI] package (**A**) is under the GNU GPLv3 license,
except for files located under `python_appimage/data` which are MIT licensed.
Thus, the produced Manylinux Python AppImages (**B**) are not GPL'd. They
contain a CPython distribution that is (mostly) under the [PSF
license][PSF_LICENSE]. Other parts of **B** (e.g. `AppRun`) are under the MIT
license.


[APPLICATIONS]: https://github.com/niess/python-appimage/tree/master/applications
[APPIMAGE]: https://appimage.org/
[GITHUB]: https://github.com/niess/python-appimage
[GRAND]: http://grand.cnrs.fr
[MANYLINUX]: https://github.com/pypa/manylinux
[PSF_LICENSE]: https://docs.python.org/3/license.html#psf-license
[PYPI]: https://pypi.org/project/python-appimage/
[READTHEDOCS]: https://python-appimage.readthedocs.io/en/latest/
[RELEASES]: https://github.com/niess/python-appimage/releases
