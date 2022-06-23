---
title: 'The Python-AppImage project'
tags:
  - AppImage
  - Linux
  - Packaging
  - Python
authors:
  - name: Valentin Niess
    orcid: 0000-0001-7148-6819
    affiliation: 1
affiliations:
 - name: Université Clermont Auvergne, CNRS/IN2P3, LPC, F-63000 Clermont-Ferrand, France.
   index: 1
date: 22 June 2022
bibliography: paper.bib
---

# Summary

Since its initial release in 1991, the Linux Kernel [@kernel] has given birth to
more than 600 hundred Linux distributions (distros). While this is an impressive
success, the diversity of Linux flavours complicates the distribution of
applications for Linux (see e.g. [@Gillmor:2014]). Thus, contrary to other
operating systems, on Linux, source distributions long prevailed over binary
(precompiled) ones. Specifically, this is still the case for the Linux Python
runtime [@python] distributed by the Python Software Foundation (PSF).
Previously, this was also the case for Python packages available from the Python
Package Index (PyPI). This situation contributed to the emergence of an
alternative Python packaging system [@anaconda] delivering ready-to-use
precompiled runtimes and packages for Linux.

Over the last decade, a change of paradigm occurred in the Linux world. Cross
distros packaging systems have emerged, the like AppImage [@appimage], Flatpak
[@flatpak] and Snap [@snap]. At the same time, the PSF encouraged the conversion
of PyPI packages from source to binary distributions, using the new `wheel`
packaging format [@wheels].

The AppImage format is of particular interest for the present discussion.
Contrary to Flatpak and Snap, AppImages do not require to install an external
package manager. AppImage applications are bundled as a single executable file
upstreamed by developpers, ready-to-use after download. However, building proper
AppImages adds some complexity on the developers side.

Technically, an AppImage is an executable file embedding a software application
over a compressed virtual filesystem (VFS). The VFS is extracted and mounted at
runtime using `libfuse` [@libfuse]. Apart from core libraries, the like `libc`,
application dependencies are directly bundled inside the AppImage. In this
context, binary compatibility usually stems down to the host glibc [@glibc]
version used at compile time. As a matter of fact, glibc is admirably backward
compatible, down to version 2.1 where symbol versioning was introduced. Thus, in
practice binary compatibility is achieved by precompiling the application and
its relevant dependencies on an *old enough* Linux distro. This is greatly
facilitated by recent container technologies, the like Docker [@docker] and
Singularity [@singularity].

In practice, producing a portable binary wheel for Linux, or packaging an
application as an AppImage, faces the same issues. Accordingly, almost identical
strategies and tools are used in both cases. In particular, the PSF has
defined standard build platforms for Linux wheels. Those are available as Docker
images from the Manylinux project [@manylinux]. These images contain
precompiled Python runtimes with binary compatibility down to glibc 2.5 (for
manylinux1, corresponding to CentOS 5).

The Python-AppImage project provides relocatable Python runtimes as AppImages.
These runtimes are extracted from the Manylinux Docker images. Consequently,
they have the exact same binary compatibility as PyPI wheels. Python AppImages
are available as rolling GitHub releases. They are updated automatically on
every Sunday using GitHub Actions.

At the core of the Python-AppImage project, there is the `python-appimage`
executable, written in pure Python, and available from PyPI using `pip install`
(down to Python 2.7). The main functionality of `python-appimage` is to relocate
an existing (system) Python installation to an AppImage. Vanilla Python is not
relocatable. Therefore, some tweaks are needed in order to run Python from an
AppImage. In particular,

- Python initialisation is slightly modified in order to set `sys.executable`
  and `sys.prefix` to the AppImage and to its temporary mount point. This is
  achieved by a small edit of the `site` package.

- The run-time search path of Linux ELF files (Python runtime, binary packages,
  shared libraries) is changed to a relative location, according to the AppImage
  VFS hierarchy. Note that `patchelf` [@patchelf] allows to edit the
  corresponding ELF entry. Thus, the Python runtime and its binary packages need
  not to be recompiled.

Besides, `python-appimage` can also build simple Python based applications
according to a recipe folder. The recipe folder contains an entry point script,
AppImage metadata and an optional `requirements.txt` Python file. The
application is built from an existing  Manylinux Python AppImage. Extra
dependencies are fetched from PyPI with `pip`. Note that they must be available
as binary wheels for the resulting AppImage to be portable.


# Statement of need

Python is among the top computing languages used nowadays. It was ranked number
one in 2021 and 2022 according to the TIOBE index [@tiobe]. In particular,
Python is widely used by the scientific community. A peculiarity of the Python
language is that it constantly evolves, owing to an Open Source community of
contributors structured by the PSF. While I personally find this very exciting
when working with Python, it comes at a price. Different projects use different
Python versions, and package requirements might conflict. This can be
circumvented by using virtual environments. For example, the `venv` package
allows one to manage different sets of requirements. However, it requires an
existing Python installation, i.e. a specific runtime version. On the contrary,
`conda` environments automate the management of both different runtime versions,
and sets of requirements. But, unfortunately Anaconda fragmented Python
packaging since, in practice, `conda` packages and Python wheels are not
(always) binary compatible.

Python-AppImage offers alternative solutions when working within the PSF context
(for `conda` based AppImages, `linuxdeploy` [@linuxdeploy] could be used).
First, Python-AppImage complements `venv` by providing ready-to-use Linux
runtimes for different Python versions. Moreover, Python AppImages can be used
as a replacement to `venv` by bundling extra (site) packages aside the runtime.
In this case, since AppImages are read-only, it can be convenient to extract
their content to a local folder (using the built-in `--appimage-extract`
option). Then, the extracted AppImage appears as a classic Python installation,
but it is relocatable. Especially, one can `pip install` additional packages to
the extracted folder, and it can be moved around, e.g. from a development host
directly to a production computing center.


# Mention

This project was born in the context of the Giant Radio Array for Neutrino
Detection (GRAND) [@grand] in order to share Python based software across
various Linux hosts: personal or office computers, computing centers, etc.
Specifically, Python AppImages were used for the neutrino sensitivity studies
presented in the GRAND whitepaper [@Alvarez-Muniz:2020].

I do not track usage of Python AppImages, which are available as simple
downloads. Therefore, I cannot provide detailed statistics. However, I am aware
of a dozen of (non scientific) Python based applications using
`python-appimage`. Besides, I personally use Python AppImages for my daily
academic work.


# Acknowledgements

We are grateful to several GitHub users for comments, feedback and contributions
to this project. In particular, we would like to thank Andy Kipp (\@anki-code),
Simon Peter (\@probonopd) and \@TheAssassin for support at the very roots of
this project. In addition, we are grateful to our colleagues from the GRAND
collaboration for beta testing Python AppImages.


# References
