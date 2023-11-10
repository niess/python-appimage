import logging


__all__ = ['debug', 'log']


# Configure the logger
logging.basicConfig(
    format='[%(asctime)s] %(message)s',
    level=logging.ERROR
)
logging.getLogger('python-appimage').setLevel(logging.INFO)


def log(task, fmt, *args):
    '''Log a standard message
    '''
    logging.getLogger('python-appimage').info('%-8s ' + fmt, task, *args)


def debug(task, fmt, *args):
    '''Report some debug information
    '''
    logging.getLogger('python-appimage').debug('%-8s ' + fmt, task, *args)


def set_level(level):
    '''Set the threshold for logs
    '''
    level = getattr(logging, level)
    logging.getLogger('python-appimage').setLevel(level)
