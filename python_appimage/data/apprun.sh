{{ shebang }}

# If running from an extracted image, then export ARGV0 and APPDIR
if [ -z "${APPIMAGE}" ]; then
    export ARGV0=$0

    self="$(readlink -f -- $0)"
    here="${self%/*}"
    export APPDIR="${APPDIR:-${here}}"
fi

# Resolve the calling command (preserving symbolic links).
export APPIMAGE_COMMAND="$(command -v -- $ARGV0)"
{{ tcltk-env }}
{{ cert-file }}

# Call the entry point
{{ entrypoint }}
