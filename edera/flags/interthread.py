from edera.flag import Flag


class InterThreadFlag(Flag):
    """
    An inter-thread flag.

    It is safe to operate this flag from multiple threads simultaneously.
    """

    def __init__(self):
        self.__raised = False

    def __repr__(self):
        return "<%s: id %x>" % (self.__class__.__name__, id(self))

    def down(self):
        self.__raised = False

    @property
    def raised(self):
        return self.__raised

    def up(self):
        self.__raised = True
