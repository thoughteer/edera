import multiprocessing

from edera.flag import Flag


class InterProcessFlag(Flag):
    """
    An inter-process flag.

    It is safe to operate this flag from multiple processes simultaneously.
    """

    def __init__(self):
        self.__event = multiprocessing.Event()

    def __repr__(self):
        return "<%s: id %x>" % (self.__class__.__name__, id(self))

    def down(self):
        self.__event.clear()

    @property
    def raised(self):
        return self.__event.is_set()

    def up(self):
        self.__event.set()
