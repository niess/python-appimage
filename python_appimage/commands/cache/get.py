from ...manylinux import ensure_image


__all__ = ['execute']


def _unpack_args(args):
    '''Unpack command line arguments
    '''
    return (args.tags, args.extract)


def execute(images, extract):
    '''Download image(s) to the cache
    '''

    for image in images:
        ensure_image(image, extract=extract)
