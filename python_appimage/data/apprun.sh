#! /bin/bash

# Export APPRUN if running from an extracted image
self="$(readlink -f -- $0)"
here="${self%/*}"
APPDIR="${APPDIR:-${here}}"

# Export TCl/Tk
export TCL_LIBRARY="${APPDIR}/usr/share/tcltk/tcl{{ tcl-version }}"
export TK_LIBRARY="${APPDIR}/usr/share/tcltk/tk{{ tk-version }}"
export TKPATH="${TK_LIBRARY}"

# Call the entry point
{{ entrypoint }}
