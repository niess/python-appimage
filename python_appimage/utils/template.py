import os
import re
import shutil

from .fs import make_tree
from .log import debug


__all__ = ['copy_template', 'load_template']


_template_pattern = re.compile('[{][{][ ]*([^{} ]+)[ ]*[}][}]')


def load_template(path, **kwargs):
    '''Load a template file and substitue keywords
    '''
    with open(path) as f:
        template = f.read()

    def matcher(m):
        tag = m.group(1)
        try:
            return kwargs[tag]
        except KeyError:
            return tag

    return _template_pattern.sub(matcher, template)


def copy_template(path, destination, **kwargs):
    '''Copy a template file and substitue keywords
    '''
    txt = load_template(path, **kwargs)

    debug('COPY', '%s as %s', os.path.basename(path), destination)
    make_tree(os.path.dirname(destination))
    with open(destination, 'w') as f:
        f.write(txt)

    shutil.copymode(path, destination)
