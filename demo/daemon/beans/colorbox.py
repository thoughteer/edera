from edera.helpers import SimpleBox

from . import threadsafe


@threadsafe
class Bean(SimpleBox):

    def __new__(cls):
        return SimpleBox()
