__all__ = ['tonumbers']


def tonumbers(s):
    '''Convert a version string to a list of numbers, for comparison
    '''
    return [int(v) for v in s.split('.')]
