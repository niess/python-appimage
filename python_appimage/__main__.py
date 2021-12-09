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
                                       help='Command to execute',
                                       dest='command')

    parser.add_argument('-q', '--quiet', help='disable logging',
        dest='verbosity', action='store_const', const=logging.ERROR)
    parser.add_argument('-v', '--verbose', help='print extra information',
        dest='verbosity', action='store_const', const=logging.DEBUG)

    install_parser = subparsers.add_parser('install',
        description='Install binary dependencies')
    install_parser.add_argument('binary', nargs='+',
        choices=binaries, help='one or more binary name')

    build_parser = subparsers.add_parser('build',
        description='Build a Python appimage')
    build_subparsers = build_parser.add_subparsers(
                           title='type',
                           help='Type of AppImage build',
                           dest='sub_command')

    build_local_parser = build_subparsers.add_parser('local',
        description='Bundle a local Python installation')
    build_local_parser.add_argument('-d', '--destination',
                              help='AppImage destination')
    build_local_parser.add_argument('-p', '--python', help='python executable')

    build_manylinux_parser = build_subparsers.add_parser('manylinux',
        description='Bundle a manylinux Python installation using docker')
    build_manylinux_parser.add_argument('tag',
        help='manylinux image tag (e.g. 2010_x86_64)')
    build_manylinux_parser.add_argument('abi',
        help='python ABI (e.g. cp37-cp37m)')

    build_manylinux_parser.add_argument('--contained', help=argparse.SUPPRESS,
                                        action='store_true', default=False)

    build_app_parser = build_subparsers.add_parser('app',
        description='Build a Python application using a base AppImage')
    build_app_parser.add_argument('appdir',
        help='path to the application metadata')
    build_app_parser.add_argument('-b', '--base-image',
        help='path to a base image on disk')
    build_app_parser.add_argument('-l', '--linux-tag',
        help='linux compatibility tag (e.g. manylinux1_x86_64)')
    build_app_parser.add_argument('-n', '--name',
        help='application name')
    build_app_parser.add_argument('--python-tag',
        help='python compatibility tag (e.g. cp37-cp37m)')
    build_app_parser.add_argument('-p', '--python-version',
        help='python version (e.g. 3.8)')
    build_app_parser.add_argument('--in-tree-build',
                                  help='force pip in-tree-build',
                                  action='store_true',
                                  default=False)

    which_parser = subparsers.add_parser('which',
        description='Locate a binary dependency')
    which_parser.add_argument('binary', choices=binaries,
        help='name of the binary to locate')

    args = parser.parse_args()

    # Configure the verbosity
    if args.verbosity:
        logging.getLogger().setLevel(args.verbosity)

    # check if no arguments are passed
    if args.command is None:
        parser.print_help()
        return

    # Call the requested command
    module = '.commands.' + args.command
    try:
        module += '.' + args.sub_command
    except AttributeError:
        pass
    command = import_module(module, package=__package__)

    # check if the module has a 'execute' subcommand
    # if not, display the help message
    if not hasattr(command, 'execute'):
        locals().get('{}_parser'.format(args.command)).print_help()
        return

    # execute the command
    command.execute(*command._unpack_args(args))


if __name__ == "__main__":
    main()
