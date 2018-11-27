from edera.demo.daemon.beans import threadsafe
from edera.helpers import SimpleBox


@threadsafe
class Bean(SimpleBox):

    def __new__(cls):
        return SimpleBox()
