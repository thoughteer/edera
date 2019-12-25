import threading
import time

import pytest

from edera.exceptions import LockAcquisitionError


def test_lock_acquisition_fails_if_zookeeper_is_down(zookeeper, zookeeper_locker):
    zookeeper.stop()
    with pytest.raises(LockAcquisitionError):
        with zookeeper_locker.lock("key"):
            pass
    zookeeper.start()


def test_lock_can_be_autoreleased_when_session_expires(zookeeper, zookeeper_locker):

    def lock_and_wait(key, lock_flag, release_flag):
        interruption_flag = threading.Event()
        with zookeeper_locker.lock(key, callback=interruption_flag.set):
            lock_flag.set()
            while not interruption_flag.is_set():
                time.sleep(0.1)
        release_flag.set()

    thread_count = 5
    keys = ["key-%d" % index for index in range(thread_count)]
    lock_flags = [threading.Event() for _ in keys]
    release_flags = [threading.Event() for _ in keys]
    threads = []
    for key, lock_flag, release_flag in zip(keys, lock_flags, release_flags):
        thread = threading.Thread(target=lock_and_wait, args=(key, lock_flag, release_flag))
        thread.daemon = True
        thread.start()
        threads.append(thread)
    for lock_flag in lock_flags:
        lock_flag.wait(1.0)
        assert lock_flag.is_set()
    zookeeper.stop()
    for release_flag in release_flags:
        release_flag.wait(5.0)
        assert release_flag.is_set()
    for thread in threads:
        thread.join(1.0)
    zookeeper.start()
