#!/bin/bash

SCRIPT="$(readlink -f -- $0)"
SCRIPTPATH="$(dirname $SCRIPT)"
APPDIR="${APPDIR:-$SCRIPTPATH/../..}"

# Configure the environment
if [ -d "${APPDIR}/usr/share/tcltk" ]; then
    export TCL_LIBRARY="$(ls -d ${APPDIR}/usr/share/tcltk/tcl* | tail -1)"
    export TK_LIBRARY="$(ls -d ${APPDIR}/usr/share/tcltk/tk* | tail -1)"
    export TKPATH="${TK_LIBRARY}"
fi

# Resolve symlinks within the image
prefix="opt/{{PYTHON}}"
nickname="{{PYTHON}}"
executable="${APPDIR}/${prefix}/bin/${nickname}"

if [ -L "${executable}" ]; then
    nickname="$(basename $(readlink -f ${executable}))"
fi

for opt in "$@"
do
    [ "${opt:0:1}" != "-" ] && break
    if [[ "${opt}" =~ "I" ]] || [[ "${opt}" =~ "E" ]]; then
        # Environment variables are disabled ($PYTHONHOME). Let's run in a safe
        # mode from the raw Python binary inside the AppImage
        "$APPDIR/${prefix}/bin/${nickname}" "$@"
        exit "$?"
    fi
done

# But don't resolve symlinks from outside!
if [[ "${ARGV0}" =~ "/" ]]; then
    executable="$(cd $(dirname ${ARGV0}) && pwd)/$(basename ${ARGV0})"
elif [[ "${ARGV0}" != "" ]]; then
    executable=$(which "${ARGV0}")
fi

# Wrap the call to Python in order to mimic a call from the source
# executable ($ARGV0), but potentially located outside of the Python
# install ($PYTHONHOME)
(PYTHONHOME="${APPDIR}/${prefix}" exec -a "${executable}" "$APPDIR/${prefix}/bin/${nickname}" "$@")
exit "$?"
