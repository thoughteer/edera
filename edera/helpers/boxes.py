import multiprocessing

from edera.helpers.box import Box
from edera.routine import routine


class MultiBox(Box):
    """
    A multi-compartment box that selects the compartment upon access.

    Very useful for creating fork-/thread-/greenlet-dependent variables.

    Example:
        Here we create a multi-box that contains different values for different processes (forks):

            >>> import os
            >>> box = MultiBox(os.getpid)
            >>> box.put(1)
            >>> box.get()
            1
            >>> # fork...
            >>> box.get() is None
            True
            >>> box.put(2)
            >>> box.get()
            2
    """

    def __init__(self, selector):
        """
        Args:
            selector (Callable[[], Hashable]) - a current key selector
                Keys must be hashable and comparable.
        """
        self.__selector = selector
        self.__values = {}

    def get(self):
        return self.__values.get(self.__selector())

    def put(self, value):
        key = self.__selector()
        if value is None:
            if key in self.__values:
                del self.__values[key]
        else:
            self.__values[key] = value


class SharedBox(Box):
    """
    A single-producer-multiple-consumers box that can be shared between forks.
    """

    def __init__(self):
        self.__queue = multiprocessing.Queue(maxsize=1)
        self.__queue.cancel_join_thread()
        self.__queue.put(None)

    @routine
    def get(self):
        value = yield self.__drain.defer()
        self.__queue.put(value)
        yield value

    @routine
    def put(self, value):
        yield self.__drain.defer()
        self.__queue.put(value)

    @routine
    def __drain(self):
        while True:
            try:
                value = self.__queue.get(timeout=1)
            except:
                yield
            else:
                yield value
                return


class SimpleBox(Box):
    """
    A straight-forward box implementation.
    """

    def __init__(self):
        self.__value = None

    def get(self):
        return self.__value

    def put(self, value):
        self.__value = value
