import os.path

from edera.demo.daemon.beans import arguments
from edera.demo.daemon.beans import colorbox
from edera.demo.daemon.beans import colorful


@colorful
class Bean(object):

    @property
    def root(self):
        color = colorbox.get()
        return arguments.root if color is None else os.path.join(arguments.root, color)
