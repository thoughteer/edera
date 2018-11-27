import pytest

from edera.exceptions import LockAcquisitionError


def test_cascade_locker_invokes_all_sublockers(cascade_locker):
    with cascade_locker.lock("key"):
        for sublocker in cascade_locker.sublockers:
            with pytest.raises(LockAcquisitionError):
                with sublocker.lock("key"):
                    pass
    for sublocker in cascade_locker.sublockers:
        with sublocker.lock("key"):
            pass


def test_cascade_locker_propagates_acquisition_errors(cascade_locker):
    with cascade_locker.sublockers[-1].lock("key"):
        with pytest.raises(LockAcquisitionError):
            with cascade_locker.lock("key"):
                pass
        for sublocker in cascade_locker.sublockers[:-1]:
            with sublocker.lock("key"):
                pass
