{{ shebang }}

# Export APPRUN if running from an extracted image
self="$(readlink -f -- $0)"
here="${self%/*}"
APPDIR="${APPDIR:-${here}}"
{{ tcltk-env }}
{{ cert-file }}

# Call the entry point
{{ entrypoint }}
