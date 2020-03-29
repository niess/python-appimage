import platform


if platform.system() != 'Linux':
    raise RuntimeError('invalid system: ' + plateform.system())
