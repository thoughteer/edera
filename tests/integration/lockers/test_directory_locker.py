import multiprocessing
import os
import signal
import time

import pytest

from edera.exceptions import LockAcquisitionError
from edera.lockers import DirectoryLocker


def test_lock_acquisition_fails_if_path_points_to_file(tmpdir):
    tmpdir.join("file").write("")
    with pytest.raises(Exception):
        with DirectoryLocker(str(tmpdir.join("file"))).lock("key"):
            pass


def test_locker_ignores_missing_key_file_on_release(tmpdir):
    with DirectoryLocker(str(tmpdir)).lock("key"):
        tmpdir.remove()


def test_sigkill_releases_locks(directory_locker):

    def lock_and_wait(ready_flag):
        with directory_locker.lock("key"):
            ready_flag.set()
            while True:
                time.sleep(1.0)

    ready_flag = multiprocessing.Event()
    target_process = multiprocessing.Process(target=lock_and_wait, args=(ready_flag,))
    target_process.daemon = True
    target_process.start()
    ready_flag.wait(10.0)
    assert ready_flag.is_set()
    with pytest.raises(LockAcquisitionError):
        with directory_locker.lock("key"):
            pass
    os.kill(target_process.pid, signal.SIGKILL)
    target_process.join()
    with directory_locker.lock("key"):
        pass
