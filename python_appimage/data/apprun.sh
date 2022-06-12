{{ shebang }}

# If running from an extracted image, then export APPDIR
if [ -z "${APPIMAGE}" ]; then
    self="$(readlink -f -- $0)"
    export APPDIR="${self%/*}"
fi

# Call the application entry point
{{ entrypoint }}
