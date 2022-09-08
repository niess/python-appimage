import sys


__all__ = ['decode', 'encode', 'find_spec']


def decode(s):
    '''Decode Python 3 bytes as str
    '''
    try:
        return s.decode()
    except Exception:
        return str(s)


def encode(s):
    '''Encode Python 3 str as bytes
    '''
    try:
        return s.encode()
    except Exception:
        return str(s)


if sys.version_info[0] == 2:
    from collections import namedtuple
    import imp

    ModuleSpec = namedtuple('ModuleSpec', ('name', 'origin'))

    def find_spec(name):
        return ModuleSpec(name, imp.find_module(name)[1])

else:
    import importlib
    try:
        find_spec = importlib.util.find_spec
    except AttributeError:
        import importlib.util
        find_spec = importlib.util.find_spec
