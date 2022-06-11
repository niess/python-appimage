{# This document describes the usage of Python AppImages, as runtimes.

   Note that some parts of this document are generated dynamically according to
   the reader's system configuration, and depending on released AppImages. The
   intent is to provide relevant examples to the reader, as well as a dynamic
   summary of available Python AppImages.
#}

{{ importjs("highlight.min") }}
{{ importjs("index") }}

{% include "references.md" %}


# Python AppImages

We provide relocatable Python runtimes for _Linux_ systems, as
[AppImages][APPIMAGE]. These runtimes have been extracted from
[manylinux][MANYLINUX] Docker images.
{{ "" | id("append-releases-list") }}

## Basic installation

Installing Python from an [AppImage][APPIMAGE] is as simple as downloading a
single file and changing its mode to executable. For example, as

{{ begin("#basic-installation-example") }}
```bash
wget https://github.com/niess/python-appimage/releases/download\
/python3.10/python3.10.2-cp310-cp310-manylinux2014_x86_64.AppImage

chmod +x python3.10.2-cp310-cp310-manylinux2014_x86_64.AppImage
```
{{ end("#basic-installation-example") }}

!!! Note
    As can be seen from the previous [example](#basic-installation-example), the
    AppImage name contains several informations. That are, the Python full
    version ({{ "3.10.2" | id("example-full-version") }}), the CPython tag
    ({{ "cp310-cp310" | id("example-python-tag") }}), the Linux compatibility
    tag ({{ "manylinux2014" | id("example-linux-tag") }}) and the machine
    architecture ({{ "x86_64" | id("example-arch-tag") }}).

!!! Caution
    One needs to **select an AppImage** that matches **system requirements**. A
    summmary of available Python AppImages is provided at the
    [bottom](#available-python-appimages) of this page.


{{ begin(".capsule") }}
### Creating a symbolic link

Since AppImages native names are rather lengthy, one might create a symbolic
link, e.g. as

{{ begin("#basic-installation-example-symlink") }}
```bash
ln -s python3.10.2-cp310-cp310-manylinux2014_x86_64.AppImage python3.10
```
{{ end("#basic-installation-example-symlink") }}

Then, executing the AppImage as
{{ "`./python3.10`" | id("basic-installation-example-execution") }} should
start a Python interactive session on _almost_ any Linux, provided that **fuse**
is supported.
{{ end(".capsule") }}

!!! Tip
    Fuse is not supported on Windows Subsytem for Linux v1 (WSL1), preventing
    AppImages direct execution. Yet, one can still extract the content of Python
    AppImages and use them, as explained in the [Advanced
    installation](#advanced-installation) section.


## Installing site packages

Site packages can be installed using `pip`, distributed with the AppImage. For
example, the following

{{ begin("#site-packages-example") }}
```bash
./python3.10 -m pip install numpy
```
{{ end("#site-packages-example") }}

installs the numpy package, where it is assumed that a symlink to the AppImage
has been previously created. When using the **basic installation** scheme, by
default Python packages are installed to your **user space**, i.e. under
`~/.local` on Linux.

!!! Note
    AppImage are read-only. Therefore, site packages cannot be directly
    installed to the AppImage. However, the AppImage can be extracted, as
    explained in the [Advanced installation](#advanced-installation) section.


{{ begin(".capsule") }}
### Alternative site packages location

One can
specify an alternative installation directory for site packages using the
`--target` option of pip. For example, the following

{{ begin("#site-packages-example-target") }}
```bash
./python3.10 -m pip install --target=$(pwd)/packages numpy
```
{{ end("#site-packages-example-target") }}

installs the numpy package besides the AppImage, in a `packages` folder.
{{ end(".capsule") }}

!!! Tip
    Packages installed in non standard locations are not automatically found by
    Python. Their location must be aded to `sys.path`, e.g. using the
    `PYTHONPATH` environment variable.

!!! Caution
    While Python AppImages are relocatable, site packages might not be. In
    particular, packages installing executable Python scripts assume a fix
    location of the Python runtime. If the Python AppImage is moved, then these
    scripts will fail. This can be patched by editing the script
    [shebang][SHEBANG], or be reinstalling the corresponding package.


## Isolating from the user environment

Python AppImages are not isolated from the user space. Therefore, by default
site packages located under `~/.local` are loaded instead of system ones.  Note
that this is the usual Python runtime behaviour. However, it can be conflictual
in some cases.

In order to disable user site packages, one can use the `-E`, `-s` or `-I`
options of the Python runtime. For example, invoking the Python AppImage as
{{ "`./python3.10 -s`" | id("user-isolation-example") }} prevents user packages
to be loaded. The `-E` option disables Python related environment variables. In
particular, it prevents packages under `PYTHONPATH` to be loaded. The `-I`
option activates both `-E` and `-s`.


## Using a virtual environement

Isolation can also be achieved with a [virtual environment][VENV]. Python
AppImages can create a `venv` using the standard syntax, e.g. as

{{ begin("#venv-example") }}
```bash
./python3.10 -m venv /path/to/new/virtual/environment
```
{{ end("#venv-example") }}

Note that moving the base Python AppImage to another location breaks the virtual
environment. This can be patched by editing symbolic links under `venv/bin`, as
well as the `home` variable in `venv/pyvenv.cfg`. The latter must point to the
AppImage directory.

!!! Tip
    Old Python AppImages, created before version 1.1, fail setting up `pip`
    automaticaly during `venv` creation. However, this can be patched by calling
    `ensurepip` from within the `venv`, after its creation.  For example, as

```bash
source /path/to/new/virtual/environment/bin/activate

python -m ensurepip
```


## Advanced installation

The [basic installation](#basic-installation) scheme described previously has
some limitations when using Python AppImages as a runtime. For example,  site
packages need to be installed to a separate location. This can be solved by
extracting a Python AppImage to an `*.AppDir` directory, e.g. as


{{ begin("#advanced-installation-example") }}
```bash
./python3.10.2-cp310-cp310-manylinux2014_x86_64.AppImage --appimage-extract

mv squashfs-root python3.10.2-cp310-cp310-manylinux2014_x86_64.AppDir

ln -s python3.10.2-cp310-cp310-manylinux2014_x86_64.AppDir/AppRun python3.10
```
{{ end("#advanced-installation-example") }}

Then, by default **site packages** are installed to the extracted **AppDir**,
when using `pip`. In addition, executable scripts installed by `pip` are patched
in order to use relative [shebangs][SHEBANG].  Consequently, the AppDir can be
freely moved around.

!!! Note
    Python AppDirs follow the [manylinux][MANYLINUX] installation scheme.
    Executable scripts are installed under `AppDir/opt/pythonX.Y/bin` where _X_
    and _Y_ in _pythonX.Y_ stand for the major and minor version numbers. Site
    packages are located under
    `AppDir/opt/pythonX.Y/lib/pythonX.Y/site-packages`.

!!! Tip
    As for Python AppImages, by default the extracted runtime is [not isolated
    from the user environment](#isolating-from-the-user-environment). This
    behaviour can be changed by editing the `AppDir/AppRun` wrapper script, and
    by adding the `-s`, `-E` or `-I` option at the very bottom, where Python is
    invoked.


{{ begin(".capsule") }}
### Repackaging the AppImage

An extracted AppDir can be re-packaged as an AppImage using
[appimagetool][APPIMAGETOOL], e.g. as


{{ begin("#repackaging-example") }}
```bash
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/\
appimagetool-x86_64.AppImage

chmod +x appimagetool-x86_64.AppImage

./appimagetool-x86_64.AppImage \
    python3.10.2-cp310-cp310-manylinux2014_x86_64.AppDir \
    python3.10.2-cp310-cp310-manylinux2014_x86_64.AppImage
```
{{ end("#repackaging-example") }}

This allows to customize your Python AppImage, for example by adding your
preferred site packages.
{{ end(".capsule") }}

!!! Note
    Python AppImages can also be used for packaging Python based applications,
    as AppImages. Additional details are provided in the [developers
    section](apps).


## Available Python AppImages

A summary of available Python AppImages [releases][RELEASES] is provided in the
[table](#appimages-download-links) below. Clicking on a badge should download
the corresponding AppImage.

{{ begin("#suggest-appimage-download") }}
!!! Caution
    According to your browser, your system would not be compatible with
    Python Appimages.
{{ end("#suggest-appimage-download") }}

{{ begin("#appimages-download-links") }}
!!! Danger
    Could not download releases metadata from {{ github_api.releases | url }}.
{{ end("#appimages-download-links") }}
