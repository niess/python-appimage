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
[AppImages][APPIMAGE]. These runtimes have been extracted from a variety of
[Manylinux][MANYLINUX] Docker images.
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
    AppImage name contains several pieces of information. This includes the
    Python full version ({{ "3.10.2" | id("example-full-version") }}), the
    [CPython tag][PEP_425] ({{ "cp310-cp310" | id("example-python-tag") }}), the
    [Linux compatibility tag][MANYLINUX] ({{ "manylinux2014" |
    id("example-linux-tag") }}) and the machine architecture ({{ "x86_64" |
    id("example-arch-tag") }}).

!!! Caution
    It is essential to **select an AppImage** that aligns with the **system's
    specifications**. An overview of the available Python AppImages is provided
    at the [bottom](#available-python-appimages) of this page.


{{ begin(".capsule") }}
### Creating a symbolic link

As AppImages' native names are quite lengthy, it might be relevant to create a
symbolic link, for example as

{{ begin("#basic-installation-example-symlink") }}
```bash
ln -s python3.10.2-cp310-cp310-manylinux2014_x86_64.AppImage python3.10
```
{{ end("#basic-installation-example-symlink") }}

Executing the AppImage as {{ "`./python3.10`" |
id("basic-installation-example-execution") }} should then start a Python
interactive session on almost any Linux distribution, provided that **fuse** is
supported.
{{ end(".capsule") }}

!!! Tip
    Fuse is not supported on Windows Subsystem for Linux v1 (WSL1), which
    prevents the direct execution of AppImages. However, it is still possible to
    extract the contents of Python AppImages and use them, as explained in the
    [Advanced installation](#advanced-installation) section.


## Installing site packages

Site packages can be installed using `pip`, which is distributed with Python
AppImages. For example, the following command

{{ begin("#site-packages-example") }}
```bash
./python3.10 -m pip install numpy
```
{{ end("#site-packages-example") }}

installs the [numpy][NUMPY] package, assuming that a symlink to the AppImage has
been created beforehand. When using this **basic installation** scheme, Python
packages are installed by default to your **user space** (i.e. under `~/.local`
on Linux).

!!! Note
    AppImages are read-only. Therefore, site packages cannot be installed
    directly to the Python AppImage. However, the AppImage can be extracted, as
    explained in the [Advanced installation](#advanced-installation) section.


{{ begin(".capsule") }}
### Alternative site packages location

The `--target option` of pip can be used to specify an alternative installation
directory for site packages. For example, the following command

{{ begin("#site-packages-example-target") }}
```bash
./python3.10 -m pip install --target=$(pwd)/packages numpy
```
{{ end("#site-packages-example-target") }}

installs the [numpy][NUMPY] package in the `packages` folder, besides the
AppImage.

{{ end(".capsule") }}

!!! Tip
    Packages installed in non standard locations are not automatically found by
    Python. Their location must be aded to `sys.path`, e.g. using the
    `PYTHONPATH` environment variable.

!!! Caution
    Although Python AppImages are relocatable, site packages may not be. In
    particular, packages that install executable Python scripts assume a fixed
    location for the Python runtime. If the Python AppImage is moved, these
    scripts will fail. This can be resolved by either editing the script
    [shebang][SHEBANG] or reinstalling the corresponding package.


## Isolating from the user environment

By default, Python AppImages are not isolated from the user environment. For
example, packages located under `~/.local/lib/pythonX.Y/site-packages` are
loaded before the AppImage's ones. Note that this is the standard Python runtime
behaviour. However, this can be conflictual for some applications.

To isolate your application from the user environment, the Python runtime
provides the `-E`, `-s` and `-I` options. For example, running {{ "`./python3.10
-s`" | id("user-isolation-example") }} prevents the loading of user site
packages located under `~/.local`. Additionally, the `-E` option disables
Python-related environment variables. In particular, it prevents packages under
`PYTHONPATH` from being loaded. The `-I` option triggers both the `-E` and `-s`
options.


## Using a virtual environement

[Virtual environments][VENV] can also be used to achieve isolation. For example,
Python AppImages can create a `venv` using the standard syntax, as

{{ begin("#venv-example") }}
```bash
./python3.10 -m venv /path/to/new/virtual/environment
```
{{ end("#venv-example") }}

Please note that moving the base Python AppImage to a different location will
break the virtual environment. This can be resolved by editing the symbolic
links in `venv/bin`, as well as the `home` variable in `venv/pyvenv.cfg`. The
latter must point to the AppImage directory.

!!! Tip
    Old Python AppImages created before version 1.1 fail to set up `pip`
    automatically during `venv` creation. However, this can be resolved by
    calling `ensurepip` within the virtual environment after its creation. For
    example, as

```bash
source /path/to/new/virtual/environment/bin/activate

python -m ensurepip
```


## Advanced installation

The [basic installation](#basic-installation) scheme described previously has
certain limitations when Python AppImages are used as the runtime environment.
For example, site packages need to be installed in a different location. This
issue can be resolved by extracting a Python AppImage to an `AppDir`
directory, e.g. as

{{ begin("#advanced-installation-example") }}
```bash
./python3.10.2-cp310-cp310-manylinux2014_x86_64.AppImage --appimage-extract

mv squashfs-root python3.10.2-cp310-cp310-manylinux2014_x86_64.AppDir

ln -s python3.10.2-cp310-cp310-manylinux2014_x86_64.AppDir/AppRun python3.10
```
{{ end("#advanced-installation-example") }}

Then, by default, **site packages** are installed to the extracted `AppDir`
when using `pip`. Additionally, executable scripts installed by `pip` are
patched to use relative [shebangs][SHEBANG]. Consequently, the `AppDir` can be
moved around freely.

!!! Note
    Python `AppDirs` follow the [Manylinux][MANYLINUX] installation scheme.
    Executable scripts are installed under the `AppDir/opt/pythonX.Y/bin`
    directory, where _X_ and _Y_ represent the major and minor version numbers,
    respectively. Site packages are located under
    `AppDir/opt/pythonX.Y/lib/pythonX.Y/site-packages`. For convenience,
    applications installed using `pip` are also mirrored under `AppDir/usr/bin`
    using symbolic links.

!!! Tip
    As for Python AppImages, the extracted runtime is [not isolated from the
    user environment](#isolating-from-the-user-environment) by default. This
    behaviour can be changed by editing the `AppDir/usr/bin/pythonX.Y` wrapper
    script and adding the `-s`, `-E` or `-I` option to the line invoking Python
    (at the end of the script).


{{ begin(".capsule") }}
### Repackaging the AppImage

An extracted `AppDir` can be re-packaged as an AppImage using
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

This allows you to personalise your Python AppImage by adding your preferred
site packages, for example.
{{ end(".capsule") }}

!!! Note
    Python AppImages can also be used to package Python-based applications as
    AppImages. Further information can be found in the [developers'
    section](apps).


## Available Python AppImages

The [table](#appimages-download-links) below provides a summary of the available
Python AppImage [releases][RELEASES]. Clicking on a badge should download the
corresponding AppImage.

{{ begin("#suggest-appimage-download") }}
!!! Caution
    According to your browser, your system would not be compatible with
    Python Appimages.
{{ end("#suggest-appimage-download") }}

{{ begin("#appimages-download-links") }}
!!! Danger
    Could not download releases metadata from {{ github_api.releases | url }}.
{{ end("#appimages-download-links") }}
