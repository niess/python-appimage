{# This document describes the usage of the python-appimage utility.

   The intended audience is developers. In addition, this document also provides
   some tips for packaging Python based applications.
#}

{{ importjs("highlight.min") }}
{{ importjs("apps") }}

{% include "references.md" %}


# Developers' corner

Python [AppImages][APPIMAGE] are created using the `python-appimage` utility,
which is available on [PyPI][PYPI]. This utility can also be used to package
Python-based applications as AppImages using an existing AppImage and a recipe
folder.

!!! Caution
    The `python-appimage` utility can only package applications that can be
    installed directly with `pip`. For more advanced usage, it is necessary to
    extract and edit the Python AppImage, as explained in the [Advanced
    installation](index.md#advanced-installation) section. Further details on
    this use case can be found [below](#advanced-packaging).


## Building a Python AppImage

The primary purpose of `python-appimage` is to relocate an existing Python
installation to an AppDir and build the corresponding AppImage. For example, the
command

```bash
python-appimage build local -p $(which python2)
```

should create an AppImage of your local Python installation, provided that it
exists.

!!! Tip
    Help on the available arguments and options for `python-appimage` can be
    obtained by using the `-h` flag. For example, running
    `python-appimage build local -h` provides help on local builds.


{{ begin(".capsule") }}
### Auxiliary tools

The `python-appimage` utility relies on auxiliary tools that are downloaded and
installed on demand during application execution. These are
[appimagetool][APPIMAGETOOL], which is used to build AppImages, and
[patchelf][PATCHELF], which is used to edit runtime paths (`RPATH`) in ELF
files. These auxiliary tools are installed in the application cache. Their
location can be found using the `which` command. For example, the command

```bash
python-appimage which appimagetool
```

returns the location of [appimagetool][APPIMAGETOOL] if it has been installed.
If not, the `install` command can be used to trigger its installation.
{{ end(".capsule") }}


## Manylinux Python AppImages

AppImages of your local `python` are unlikely to be portable, unless you are
running an outdated Linux distribution. A core component that prevents
portability across Linux distributions is the use of different versions of the
`glibc` system library. Fortunately, `glibc` is highly backward compatible.
Therefore, a simple workaround is to compile binaries using the oldest Linux
distribution you can. This strategy is used to create portable AppImages and to
distribute Python site packages as ready-to-use binary [wheels][WHEELS].

The Python Packaging Authority (PyPA) has defined standard platform tags for
building Python site packages labelled [Manylinux][MANYLINUX]. These build
platforms are available as Docker images, with different versions of Python
already installed. The `python-appimage` utility can be used to package these
installations as AppImages. For example, the following command

```bash
python-appimage build manylinux 2014_x86_64 cp313-cp313
```

should build an AppImage of Python __3.13__ using the CPython (__cp313-cp313__)
installation found in the `manylinux2014_x86_64` Docker image.

!!! Note
    From version `1.4.0` of `python-appimage` onwards, Docker is **no longer**
    required to build the Manylinux Python images. Cross-building is also
    supported, for example producing an `aarch64` Python image from an `x86_64`
    host.

!!! Warning
    Creating multiple Manylinux Python images can significantly increase the
    size of the application cache. This can be managed using the
    `python-appimage cache` command.

!!! Tip
    A compilation of ready-to-use Manylinux Python AppImages is available in the
    [releases][RELEASES] section of the `python-appimage` [GitHub
    repository][GITHUB]. These AppImages are updated weekly, on every Sunday.

!!! Tip
    Instead of an AppImage, the `python-appimage build manylinux` command can
    produce either an `AppDir` or a bare tarball (i.e. without the AppImage
    layer) of a Manylinux Python installation. See the `-b` and `-n` command
    line options for more information.

## Simple packaging

The `python-appimage` utility can also be used to package simple AppImage
applications, whose dependencies can be installed using `pip`. The syntax is

```bash
python-appimage build app -p 3.13 /path/to/recipe/folder
```

to build a Python 3.13-based application from a recipe folder. Examples of
recipes can be found in the [applications][APPLICATIONS] folder on GitHub. The
recipe folder contains

- the AppImage metadata (`application.xml` and `application.desktop`),
- an application icon (e.g. `application.png`),
- a Python requirements file (`requirements.txt`),
- an entry point script (`entrypoint.sh`).

Further information on metadata can be found in the AppImage documentation
(e.g., regarding [desktop][APPIMAGE_DESKTOP] and [AppStream XML][APPIMAGE_XML]
files). The `requirements.txt` file enables additional site packages to be
specified for bundling in the AppImage using `pip`.

!!! Caution
    In order for the application to be portable, the site packages bundled in
    the AppImage and their dependencies must be available as binary wheels or
    pure Python packages.

    If a **C extension** is bundled from **source**, it will likely **not be
    portable**; this is discussed further in the [Advanced
    packaging](#advanced-packaging) section.

!!! Tip
    Some site packages are only available for specific Manylinux tags. You can
    check this by browsing the `Download files` section on the package's PyPI
    page.

!!! Tip
    Since version 1.2, `python-appimage` allows local requirements to be
    specified using the `local+` tag (see
    [PR49](https://github.com/niess/python-appimage/pull/49)). Please note,
    however, that this involves directly copying the local package, which has
    several limitations.

{{ begin(".capsule") }}
### Entry point script

{% raw %}
The entry point script deserves some additional explanations. This script lets
you customise your application's startup. A typical `entrypoint.sh` script would
look like this

```bash
{{ python-executable }} ${APPDIR}/opt/python{{ python-version }}/bin/my_app.py "$@"
```

where `my_app.py` is the application startup script installed by `pip`. As can
be seen from the previous example, the `entrypoint.sh` script recognises
particular variables nested between double curly braces (`{{}}`). These
variables are listed in the table below. In addition, the usual [AppImage
environement variables][APPIMAGE_ENV] can be used if needed. For instance,
`$APPDIR` points to the AppImage mount point at runtime.
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
    By default, Python AppImages are not isolated from user space or
    Python-specific environment variables such as `PYTHONPATH`. Depending on
    your use case, this can cause problems.

    You can change the isolation level by adding the `-E`, `-s` or `-I` options
    when invoking the runtime. For example, `{{ python-executable }} -I` starts
    a fully isolated Python instance.
{% endraw %}

### Bundling data files

`python-appimage` is also capable of bundling auxiliary data files directly into
the resulting AppImage. The `-x/--extra-data` switch is used for this purpose.
Consider the following example.

```bash
echo -n "foo" > foo
mkdir bar
echo -n "baz" > bar/baz
python-appimage [your regular parameters] -x foo bar/*
```

In this way, user data becomes accessible to the Python code contained within
the AppImage as regular files under the directory pointed to by the `APPDIR`
environment variable. An example of a Python 3 script that reads these files is
presented below.

```python
import os, pathlib
for fileName in ("foo", "baz"):
  print((pathlib.Path(os.getenv("APPDIR")) / fileName).read_text())
```

When executed, the above code would produce the following output.

```bash
foo
baz
```

## Advanced packaging

In more complex cases, for example if your application relies on external C
libraries that are not bundled with the Python runtime, the simple packaging
scheme described previously will not work. This falls outside the scope of
`python-appimage`, which is primarily intended for relocating an existing Python
installation. In this case, you may wish to refer to the initial AppImage
[Packaging Guide][APPIMAGE_PACKAGING], and use alternative tools such as
[linuxdeploy][LINUXDEPLOY].

However, `python-appimage` can still be useful in more complex cases, as it can
generate a base AppDir containing a relocatable Python runtime (e.g., using the
`-n` option). This can then serve as a starting point to create more complex
AppImages.

!!! Tip
    In some cases, a simple workaround for missing external libraries is to
    download portable versions of them from a Manylinux distribution and bundle
    them in `AppDir/usr/lib`. You may also need to edit the dynamic section
    using [`patchelf`][PATCHELF], which is installed by `python-appimage`.


{{ begin(".capsule") }}
### C extension modules

If your application relies on C extension modules, these must be compiled on a
Manylinux distribution in order to be portable. Their dependencies also need to
be bundled. In this case, it would be better to start by building a binary wheel
of your package using tools like [Auditwheel][AUDITWHEEL], which can automate
some parts of the packaging process. Please note that `auditwheel` is already
installed on the Manylinux Docker images.

Once you have built a binary wheel of your package, you can use it with
`python-appimage` to package your application as an AppImage.
{{ end(".capsule") }}
