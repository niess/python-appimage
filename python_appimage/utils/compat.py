__all__ = ['decode']


def decode(s):
    '''Decode Python 3 bytes as str
    '''
    try:
        return s.decode()
    except AttributeError:
        return str(s)
