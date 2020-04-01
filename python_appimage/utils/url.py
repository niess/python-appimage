import os
try:
    from urllib.request import urlopen as _urlopen
except ImportError:
    from urllib2 import urlopen as _urlopen
try:
    from urllib.request import urlretrieve as _urlretrieve
except ImportError:
    import urllib2
    _urlretrieve = None

from .log import debug


__all__ = ['urlopen', 'urlretrieve']


def urlopen(url, *args, **kwargs):
    '''Open a remote file
    '''
    baseurl, urlname = os.path.split(url)
    debug('DOWNLOAD', '%s from %s', baseurl, urlname)
    return _urlopen(url, *args, **kwargs)


def urlretrieve(url, filename=None):
    '''Download a file to disk
    '''
    if filename is None:
        filename = os.path.basename(url)
        debug('DOWNLOAD', '%s from %s', name, os.path.dirname(url))
    else:
        debug('DOWNLOAD', '%s as %s', url, filename)

    if _urlretrieve is None:
        data = urllib2.urlopen(url).read()
        with open(filename, 'w') as f:
            f.write(data)
    else:
        _urlretrieve(url, filename)
