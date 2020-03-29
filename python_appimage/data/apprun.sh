#! /bin/bash

# Export APPRUN if running from an extracted image
self="$(readlink -f -- $0)"
here="${self%/*}"
APPDIR="${APPDIR:-${here}}"

# Call the python wrapper
"${APPDIR}/usr/bin/python{{version}}" "$@"
