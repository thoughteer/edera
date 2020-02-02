import os.path

from . import arguments
from . import colorbox
from . import colorful


@colorful
class Bean(object):

    @property
    def root(self):
        color = colorbox.get()
        return arguments.root if color is None else os.path.join(arguments.root, color)
