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


## Manylinux Python AppImages

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

The `python-appimage` utility can also be used in order to build simple
applications, that can be `pip` installed. The syntax is

```bash
python-appimage build app -p 3.10 /path/to/recipe/folder
```

in order to build a Python 3.10 based application from a recipe folder.
Examples of recipes can be found on GitHub in the [applications][APPLICATIONS]
folder.  The recipe folder contains:

- the AppImage metadata (`application.xml` and `application.desktop`),
- an application icon (e.g. `application.png`),
- a Python requirements file (`requirements.txt`)
- an entry point script (`entrypoint.sh`).

Additional information on metadata can be found in the AppImage documentation.
That is, for [desktop][APPIMAGE_DESKTOP] and [AppStream XML][APPIMAGE_XML]
files. The `requirements.txt` file allows to specify additional site packages
to be bundled in the AppImage, using `pip`.

!!! Caution
    For the application to be portable, site packages bundled in the AppImage,
    as well as their dependencies, must must be available as binary wheels, or
    be pure Python packages.

    If a **C extension** is bundled from **source**, then it will likely **not
    be portable**, as further discussed in the [Advanced
    packaging](#advanced-packaging) section.

!!! Tip
    Some site packages are available only for specific Manylinux tags. This can
    be cross-checked by browsing the `Download files` section on the package's
    PyPI page.

!!! Tip
    Since version 1.2, `python-appimage` allows to specify local requirements as
    well, using the `local+` tag (see
    [PR49](https://github.com/niess/python-appimage/pull/49)). Note however that
    this performs a direct copy of the local package, which has several
    limitations.

{{ begin(".capsule") }}
### Entry point script

{% raw %}
The entry point script deserves some additional explanations. This script allows
to customize the startup of your application. A typical `entrypoint.sh` script
would look like

```bash
{{ python-executable }} ${APPDIR}/opt/python{{ python-version }}/bin/my_app.py "$@"
```

where `my_app.py` is the application startup script, installed by `pip`. As can
be seen from the previous example, the `entrypoint.sh` script recognises some
particular variables, nested between double curly braces, `{{ }}`. Those
variables are listed in the table hereafter. In addition, usual [AppImage
environement variables][APPIMAGE_ENV] can be used as well, if needed. For
example, `$APPDIR` points to the AppImage mount point at runtime.
{% endraw %}

| variable             | Description                                                   |
|----------------------|---------------------------------------------------------------|
| `architecture`       | The AppImage architecture, e.g. `x86_64`.                     |
| `linux-tag`          | The Manylinux compatibility tag, e.g. `manylinux2014_x86_64`. |
| `python-executable`  | Path to the AppImage Python runtime.                          |
| `python-fullversion` | The Python full version string, e.g. `3.10.2`.                |
| `python-tag`         | The Python compatibility tag, e.g. `cp310-cp310`.             |
| `python-version`     | The Python short version string, e.g. `3.10`.                 |
{{ end(".capsule") }}

{% raw %}
!!! Note
    By default, Python AppImages are not isolated from the user space, nor from
    Python specific environment variables, the like `PYTHONPATH`. Depending on
    your use case, this can be problematic.

    The runtime isolation level can be changed by adding the `-E`, `-s` or `-I`
    options, when invoking the runtime.  For example,
    `{{ python-executable }} -I` starts a fully isolated Python instance.
{% endraw %}

### Bundling data files

`python-appimage` is also capable of bundling in auxilliary data files directly
into the resulting AppImage. `-x/--extra-data` switch exists for that task.
Consider following example.

```bash
echo -n "foo" > foo
mkdir bar
echo -n "baz" > bar/baz
python-appimage [your regular parameters] -x foo bar/*
```

User data included in such a way becomes accessible to the Python code
contained within the AppImage in a form of regular files under the directory
pointed to by `APPDIR` environment variable. Example of Python 3 script
that reads these exemplary files is presented below.

```python
import os, pathlib
for fileName in ("foo", "baz"):
  print((pathlib.Path(os.getenv("APPDIR")) / fileName).read_text())
```

Above code, when executed, would print following output.

```bash
foo
baz
```

## Advanced packaging

In more complex cases, e.g. if your application relies on external C libraries
not bundled with the Python runtime, then the simple packaging scheme described
previously will fail. Indeed, this falls out of the scope of `python-appimage`,
whose main purpose it to relocate an existing Python install. In this case, you
might rather refer to the initial AppImage [Packaging
Guide][APPIMAGE_PACKAGING], and use alternative tools like
[linuxdeploy][LINUXDEPLOY].

However, `python-appimage` can still be of use in more complex cases by
extracting its AppImages to an AppDir, as discussed in the [Advanced
installation](index.md#advanced-installation) section. The extracted AppImages
contain a relocatable Python runtime, that can be used as a starting base for
building more complex AppImages.

!!! Tip
    In some cases, a simple workaround to missing external libraries can be to
    fetch portable versions of those from a Manylinux distro, and to bundle them
    under `AppDir/usr/lib`. You might also need to edit their dynamic section,
    e.g.  using [`patchelf`][PATCHELF], which is installed by `python-appimage`.


{{ begin(".capsule") }}
### C extension modules

If your application relies on C extension modules, they need to be compiled on a
Manylinux distro in order to be portable. In addition, their dependencies need
to be bundled as well. In this case, you might better start by building a binary
wheel of your package, using tools like [Auditwheel][AUDITWHEEL] which can
automate some parts of the packaging process. Note that `auditwheel` is already
installed on the Manylinux Docker images.

Once you have built a binary wheel of your package, it can be used with
`python-appimage` in order to package your application as an AppImage.
{{ end(".capsule") }}
