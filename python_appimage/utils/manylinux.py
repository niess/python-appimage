def format_appimage_name(abi, version, tag):
    '''Format the Python AppImage name using the ABI, python version and OS tags
    '''
    return 'python{:}-{:}-{:}.AppImage'.format(
        version, abi, format_tag(tag))


def format_tag(tag):
    '''Format Manylinux tag
    '''
    if tag.startswith('2_'):
        return 'manylinux_' + tag
    else:
        return 'manylinux' + tag
