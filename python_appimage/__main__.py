import argparse
from importlib import import_module
import logging
import os
import sys

from .deps import fetch_all


__all__ = ['main']


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Bundle a Python install into an AppImage')
    subparsers = parser.add_subparsers(title='builder',
                                       help='Appimage builder',
                                       dest='builder')

    parser.add_argument('-q', '--quiet', help='disable logging',
        dest='verbosity', action='store_const', const=logging.ERROR)
    parser.add_argument('-v', '--verbose', help='print extra information',
        dest='verbosity', action='store_const', const=logging.DEBUG)

    parser.add_argument('--deploy', help=argparse.SUPPRESS,
                        action='store_true', default=False)

    local_parser = subparsers.add_parser('local')
    local_parser.add_argument('-d', '--destination',
                              help='AppImage destination')
    local_parser.add_argument('-p', '--python', help='python executable')

    manylinux_parser = subparsers.add_parser('manylinux')
    manylinux_parser.add_argument('tag', help='manylinux image tag')
    manylinux_parser.add_argument('abi', help='python ABI')

    manylinux_parser.add_argument('--contained', help=argparse.SUPPRESS,
                                  action='store_true', default=False)

    args = parser.parse_args()

    # Configure the verbosity
    if args.verbosity:
        logging.getLogger().setLevel(args.verbosity)

    if args.deploy:
        # Fetch dependencies and exit
        fetch_all()
        sys.exit(0)

    # Call the AppImage builder
    builder = import_module('.' + args.builder, package=__package__)
    builder.build(*builder._unpack_args(args))


if __name__ == "__main__":
    main()
