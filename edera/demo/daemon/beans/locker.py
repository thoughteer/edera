import os.path

from edera.demo.daemon.beans import arguments
from edera.lockers import DirectoryLocker


class Bean(DirectoryLocker):

    def __new__(cls):
        return DirectoryLocker(os.path.join(arguments.root, "locks"))
