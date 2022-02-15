<!-- This document describes the usage of Python AppImages, as runtimes.

Note that some parts of this document are generated dynamically according to the
reader's system configuration, and depending on released AppImages. The intent
is to provide relevant examples to the reader, as well as a dynamic summary of
available Python AppImages.
-->

<script src="js/highlight.min.js" defer></script>
<script src="js/index.js" defer></script>


# Python AppImages

We provide relocatable Python runtimes for _Linux_ systems, as
[AppImages][APPIMAGE]. These runtimes have been extracted from
[manylinux][MANYLINUX] Docker images.
{.justify .append-releases-list}

## Basic installation

Installing Python from an [AppImage][APPIMAGE] is as simple as downloading a
single file and changing its mode to executable. For example, as
{.justify}

``` { .bash #basic-installation-example }
wget https://github.com/niess/python-appimage/releases/download\
/python3.10/python3.10.2-cp310-cp310-manylinux2014_x86_64.AppImage

chmod +x python3.10.2-cp310-cp310-manylinux2014_x86_64.AppImage
```

!!! Note
    As can be seen from the previous [example](#basic-installation-example), the
    AppImage name contains several informations. That are, the Python full
    version (*3.10.2*{#example-full-version}), the CPython tag
    (*cp310-cp310*{#example-python-tag}), the Linux compatibility tag
    (*manylinux2014*{#example-linux-tag}) and the machine architecture
    (*x86_64*{#example-arch-tag}).
    {.justify}

!!! Caution
    One needs to **select an AppImage** that matches **system requirements**. A
    summmary of available Python AppImages is provided at the
    [bottom](#available-python-appimages) of this page.
    {.justify}


<div markdown="1" class="capsule">
### Creating a symbolic link

Since AppImages native names are rather lengthy, one might create a symbolic
link, e.g. as
{.justify}

``` { .bash #basic-installation-example-symlink }
ln -s python3.10.2-cp310-cp310-manylinux2014_x86_64.AppImage python3.10
```

Then, executing the AppImage as
`./python3.10`{#basic-installation-example-execution .inline} should start a
Python interactive session on _almost_ any Linux, provided that **fuse** is
supported.
{.justify}
</div>


!!! Tip
    Fuse is not supported on Windows Subsytem for Linux v1 (WSL1), preventing
    AppImages direct execution. Yet, one can still extract the content of Python
    AppImages and use them, as explained in the [Advanced
    installation](#advanced-installation) section.
    {.justify}


## Installing site packages

Site packages can be installed using `pip`{.inline}, distributed with the
AppImage. For example, the following
{.justify}

``` {.bash #site-packages-example}
./python3.10 -m pip install numpy
```

installs the numpy package, where it is assumed that a symlink to the AppImage
has been previously created. When using the **basic installation** scheme, by
default Python packages are installed to your **user space**, i.e. under
`~/.local`{.inline} on Linux.
{.justify}

!!! Note
    AppImage are read-only. Therefore, site packages cannot be directly
    installed to the AppImage. However, the AppImage can be extracted, as
    explained in the [Advanced installation](#advanced-installation) section.
    {.justify}


<div markdown="1" class="capsule">
### Alternative site packages location

One can
specify an alternative installation directory for site packages using the
`--target`{.inline .language-bash} option of pip. For example, the following
{.justify}

``` {.bash #site-packages-example-target}
./python3.10 -m pip install --target=$(pwd)/packages numpy
```

installs the numpy package besides the AppImage, in a `packages`{.inline}
folder.
{.justify}
</div>

!!! Tip
    Packages installed in non standard locations are not automatically
    found by Python. Their location must be aded to
    `sys.path`{.inline .language-python}, e.g. using the
    `PYTHONPATH`{.inline .language-bash} environment variable.
    {.justify}

!!! Caution
    While Python AppImages are relocatable, site packages might not be. In
    particular, packages installing executable Python scripts assume a fix
    location of the Python runtime. If the Python AppImage is moved, then these
    scripts will fail. This can be patched by editing the script
    [shebang][SHEBANG], or be reinstalling the corresponding package.
    {.justify}


## Isolating from the user space

Python AppImages are not isolated from the user space. Therefore, by default
site packages located under `~/.local`{.inline} are loaded instead of system
ones.  Note that this is the usual Python runtime behaviour. However, it can be
conflictual in some cases.
{.justify}

In order to disable user site packages, one can use the
`-s`{.inline .language-bash} option of the Python runtime. For example,
invoking the Python AppImage as
`./python3.10 -s`{.inline .language-bash #user-isolation-example} prevents user
packages to be loaded.
{.justify}


## Using a virtual environement

Isolation can also be achieved with a [virtual environment][VENV]. Python
AppImages can create a `venv`{.inline} using the standard syntax, e.g. as
{.justify}

``` {.bash #venv-example}
./python3.10 -m venv /path/to/new/virtual/environment
```

However, the virtual environment fails setting up `pip`{.inline}, despite the
latter is packaged with the AppImage. Yet, this can be patched by calling
`ensurepip`{.inline} from within the `venv`{.inline}, after its creation. For
example, as
{.justify}

```bash
source /path/to/new/virtual/environment/bin/activate

python -m ensurepip
```


## Advanced installation

The [basic installation](#basic-installation) scheme described previously has
some limitations when using Python AppImages as a runtime. For example,  site
packages need to be installed to a separate location. This can be solved by
extracting a Python AppImage to an `*.AppDir`{.inline} directory, e.g. as
{.justify}

``` {.bash #advanced-installation-example}
./python3.10.2-cp310-cp310-manylinux2014_x86_64.AppImage --appimage-extract

mv squashfs-root python3.10.2-cp310-cp310-manylinux2014_x86_64.AppDir

ln -s python3.10.2-cp310-cp310-manylinux2014_x86_64.AppDir/AppRun python3.10
```

Then, by default **site packages** are installed to the extracted **AppDir**,
when using `pip`{.inline}. In addition, executable scripts installed by
`pip`{.inline} are patched in order to use relative [shebangs][SHEBANG].
Consequently, the AppDir can be freely moved around.
{.justify}

!!! Note
    Python AppDirs follow the [manylinux][MANYLINUX] installation scheme.
    Executable scripts are installed under `AppDir/opt/pythonX.Y/bin`{.inline}
    where _X_ and _Y_ in _pythonX.Y_ stand for the major and minor version
    numbers. Site packages are located under
    `AppDir/opt/pythonX.Y/lib/pythonX.Y/site-packages`{.inline}.
    {.justify}

!!! Tip
    As for Python AppImages, by default the extracted runtime is [not isolated
    from the user space](#isolating-from-the-user-space). This behaviour can be
    changed by editing the `AppDir/AppRun`{.inline} wrapper script, and by
    adding the `-s`{.inline .language-bash} option at the very bottom, where
    Python is invoked.
    {.justify}


<div markdown="1" class="capsule">
### Repackaging the AppImage

An extracted AppDir can be re-packaged as an AppImage using
[appimagetool][APPIMAGETOOL], e.g. as
{.justify}

``` {.bash #repackaging-example}
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/\
appimagetool-x86_64.AppImage

chmod +x appimagetool-x86_64.AppImage

./appimagetool-x86_64.AppImage \
    python3.10.2-cp310-cp310-manylinux2014_x86_64.AppDir \
    python3.10.2-cp310-cp310-manylinux2014_x86_64.AppImage
```

This allows to customize your Python AppImage, for example by adding your
preferred site packages.
{.justify}
</div>

!!! Note
    Python AppImages can also be used for packaging Python based applications,
    as AppImages. Additional details are provided in the [developers
    section](apps).
    {.justify}


## Available Python AppImages

A summary of available Python AppImages [releases][RELEASES] is provided in the
[table](#appimages-download-links) below. Clicking on a badge should download
the corresponding AppImage.

!!! Caution
    According to your browser, your system would not be compatible with Python
    Appimages.
    {.justify #suggest-appimage-download}

<div id="appimages-download-links">
    <p style="color: red; text-align: center">
        &lt;could not download release data from
        https://github.com/niess/python-appimage/releases&gt;
    </p>
</div>


[APPIMAGE]: https://appimage.org
[APPIMAGETOOL]: https://appimage.github.io/appimagetool
[MANYLINUX]: https://github.com/pypa/manylinux
[RELEASES]: https://github.com/niess/python-appimage/releases
[SHEBANG]: https://en.wikipedia.org/wiki/Shebang_(Unix)
[VENV]: https://docs.python.org/3/library/venv.html
