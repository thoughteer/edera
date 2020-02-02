import os.path

from edera.lockers import DirectoryLocker

from . import arguments


class Bean(DirectoryLocker):

    def __new__(cls):
        return DirectoryLocker(os.path.join(arguments.root, "locks"))
