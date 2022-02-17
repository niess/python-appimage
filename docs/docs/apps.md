{# This document describes the usage of the python-appimage utility.

   The intended audience is developers. In addition, this document also provides
   some tips for packaging Python based applications.
#}

{{ importjs("highlight.min") }}
{{ importjs("apps") }}

{% include "references.md" %}


# Developers corner

Python [AppImages][APPIMAGE] are built with the `python-appimage` utility,
available from [PyPI][PYPI]. This utility can also help packaging Python based
applications as AppImages, using an existing Python AppImage and a recipe
folder.

!!! Caution
    The `python-appimage` utility can only package applications that can be
    directly installed with `pip`. For more advanced usage, one needs to extract
    the Python AppImage and to edit it, e.g. as explained in the [Advanced
    installation](index.md#advanced-installation) section.  Additional details
    on this use case are provided [below](#advanced-packaging).


## Building a Python AppImage

The primary scope of `python-appimage` is to relocate an existing Python
installation inside an AppDir, and to build the corresponding AppImage.  For
example, the following

```bash
python-appimage build local -p $(which python2)
```

should build an AppImage of your local Python 2 installation, provided that it
exists.

!!! Tip
    Help on available arguments and options to `python-appimage` can be obtained
    with the `-h` flag. For example, `python-appimage build local -h` provides
    help on local builds.


{{ begin(".capsule") }}
### Auxiliary tools

The `python-appimage` utility relies on auxiliary tools that are downloaded and
installed at runtime, on need. Those are [appimagetool][APPIMAGETOOL] for
building AppImages, and [patchelf][PATCHELF] in order to edit ELFs runtime paths
(`RPATH`). Auxiliary tools are installed to the the user space. One can get
their location with the `which` command word. For example,

```bash
python-appimage which appimagetool
```

returns the location of `appimagetool`, if it has been installed. If not, the
`install` command word can be used in order to trigger its installation.
{{ end(".capsule") }}


## Manylinux Python AppImage

AppImages of your local `python` are unlikely to be portable, except if you run
an ancient Linux distribution. Indeed, a core component preventing portability
across Linuses is the use of different versions of the `glibc` system library.
Hopefully, `glibc` is highly backward compatible. Therefore, a simple
work-around is to compile binaries using the oldest Linux distro you can afford
to.  This is the strategy used for creating portable AppImages, as well as for
distributing Python site packages as ready-to-use binary [wheels][WHEELS].

The Python Packaging Authority (PyPA) has defined standard platform tags for
building Python site packages, labelled [manylinux][MANYLINUX].  These build
platforms are available as Docker images with various versions of Python already
installed. The `python-appimage` utility can be used to package those installs
as AppImages. For example, the following command

```bash
python-appimage build manylinux 2014_x86_64 cp310-cp310
```

should build an AppImage of Python 3.10 using the CPython (_cp310-cp310_)
install found in the `manylinux2014_x86_64` Docker image.

!!! Note
    Docker needs to be already installed on your system in order to build
    Manylinux Python images. However, the command above can be run on the host.
    That is, you need **not** to explictly shell inside the manylinux Docker
    image.

!!! Tip
    A compilation of ready-to-use Manylinux Python AppImages is available from
    the [releases][RELEASES] area of the `python-appimage` [GitHub
    repository][GITHUB]. These AppImages are updated weekly, on every Sunday.


## Simple packaging

The recipe folder contains
the app metadata, a Python requirements file and an entry point script. Examples
of recipes can be found on GitHub in the [applications][APPLICATIONS] folder.


## Advanced packaging

Alternatively, you can also manualy extract one of the Python
[AppImages][APPIMAGE] as explained above and directly modify the content, e.g.
`pip install` your custom packages. Then, simply rebuild the AppImage using your
favourite tool, e.g.  [appimagetool][APPIMAGETOOL], [linuxdeploy][LINUXDEPLOY]
or `python-appimage`.
