import contextlib

import pytest

from edera import Locker
from edera.exceptions import LockAcquisitionError
from edera.lockers import CascadeLocker


class SimpleLocker(Locker):

    def __init__(self):
        self.__locked_keys = set()

    @contextlib.contextmanager
    def lock(self, key, callback=None):
        if key in self.__locked_keys:
            raise LockAcquisitionError(key)
        self.__locked_keys.add(key)
        try:
            yield
        finally:
            self.__locked_keys.remove(key)


@pytest.fixture
def cascade_locker():
    return CascadeLocker(*[SimpleLocker() for _ in range(5)])
