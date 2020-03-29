import argparse
from importlib import import_module
import logging
import os
import sys


__all__ = ['main']


def main():
    '''Entry point for the CLI
    '''

    # Binary dependencies
    binaries = ('appimagetool', 'patchelf')


    # Parse arguments
    parser = argparse.ArgumentParser(
        prog='python-appimage',
        description='Bundle a Python installation into an AppImage')
    subparsers = parser.add_subparsers(title='command',
                                       help='Build or install command',
                                       dest='command')

    parser.add_argument('-q', '--quiet', help='disable logging',
        dest='verbosity', action='store_const', const=logging.ERROR)
    parser.add_argument('-v', '--verbose', help='print extra information',
        dest='verbosity', action='store_const', const=logging.DEBUG)

    install_parser = subparsers.add_parser('install',
        description='Install binary dependencies')
    install_parser.add_argument('binary', nargs='+',
        choices=binaries, help='one or more binary name')

    local_parser = subparsers.add_parser('local',
        description='Bundle a local Python installation')
    local_parser.add_argument('-d', '--destination',
                              help='AppImage destination')
    local_parser.add_argument('-p', '--python', help='python executable')

    manylinux_parser = subparsers.add_parser('manylinux',
        description='Bundle a manylinux Python installation using docker')
    manylinux_parser.add_argument('tag',
        help='manylinux image tag (e.g. 2010_x86_64)')
    manylinux_parser.add_argument('abi',
        help='python ABI (e.g. cp37-cp37m)')

    manylinux_parser.add_argument('--contained', help=argparse.SUPPRESS,
                                  action='store_true', default=False)

    which_parser = subparsers.add_parser('which',
        description='Locate a binary dependency')
    which_parser.add_argument('binary', choices=binaries,
        help='name of the binary to locate')

    args = parser.parse_args()

    # Configure the verbosity
    if args.verbosity:
        logging.getLogger().setLevel(args.verbosity)

    # Call the requested command
    command = import_module('.commands.' +
                            args.command, package=__package__)
    command.execute(*command._unpack_args(args))


if __name__ == "__main__":
    main()
