"""Hook for cleaning the paths detected by Python
"""
import os
import sys


def clean_path():
    site_packages = "/usr/local/lib/python{:}.{:}/site-packages".format(
        *sys.version_info[:2])
    binaries_path = "/usr/local/bin"
    env_path = os.getenv("PYTHONPATH")
    if env_path is None:
        env_path = []
    else:
        env_path = [os.path.realpath(path) for path in env_path.split(":")]

    if ((os.path.dirname(sys.executable) != binaries_path) and
        (site_packages not in env_path)):
        # Remove the builtin site-packages from the path
        try:
            sys.path.remove(site_packages)
        except ValueError:
            pass


clean_path()
