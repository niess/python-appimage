# This is a site.py patch when calling Python from an AppImage.
def _initappimage():
    """Initialise executable name for running from an AppImage."""
    env = os.environ
    try:
        command = env["APPIMAGE_COMMAND"]
    except KeyError:
        return

    if command and ("APPDIR" in env):
        command = os.path.abspath(command)
        sys.executable = command
        sys._base_executable = command

_initappimage()
del _initappimage
