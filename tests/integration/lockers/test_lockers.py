import pytest

from edera.exceptions import LockAcquisitionError


def test_locker_can_lock(locker):
    with locker.lock("key"):
        pass


def test_double_lock_acquisition_fails(locker):
    with locker.lock("key"):
        with pytest.raises(LockAcquisitionError):
            with locker.lock("key"):
                pass
        with pytest.raises(LockAcquisitionError):
            with locker.lock("key"):
                pass


def test_lock_can_be_reacquired_after_release(locker):
    with locker.lock("key"):
        pass
    with locker.lock("key"):
        pass


def test_different_keys_can_be_locked_simultaneously(locker):
    with locker.lock("key-1"):
        with locker.lock("key-2"):
            pass
