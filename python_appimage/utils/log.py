import logging


__all__ = ['debug', 'log']


# Configure the logger
logging.basicConfig(
    format='[%(asctime)s] %(message)s',
    level=logging.INFO
)


def log(task, fmt, *args):
    '''Log a standard message
    '''
    logging.info('%-8s ' + fmt, task, *args)


def debug(task, fmt, *args):
    '''Report some debug information
    '''
    logging.debug('%-8s ' + fmt, task, *args)
