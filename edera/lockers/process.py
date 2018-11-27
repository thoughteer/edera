import contextlib
import threading

from edera.exceptions import LockAcquisitionError
from edera.locker import Locker


class ProcessLocker(Locker):
    """
    A process-level locker.

    A process-level lock works as an inter-thread mutex.
    You should use the same instance of the locker in spawned threads in order to make it work.
    """

    def __init__(self):
        self.__locked_keys = set()
        self.__mutex = threading.Lock()

    def __repr__(self):
        return "<%s: id %x>" % (self.__class__.__name__, id(self))

    @contextlib.contextmanager
    def lock(self, key, callback=None):
        with self.__mutex:
            if key in self.__locked_keys:
                raise LockAcquisitionError(key)
            self.__locked_keys.add(key)
        try:
            yield
        finally:
            with self.__mutex:
                self.__locked_keys.remove(key)
