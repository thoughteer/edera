import threading

from edera.exceptions import LockAcquisitionError


def test_locker_is_multithreaded(multithreaded_locker):

    def try_to_lock(key, lock_flag, fail_flag):
        try:
            with multithreaded_locker.lock(key):
                lock_flag.set()
                fail_flag.wait(3.0)
        except LockAcquisitionError:
            fail_flag.set()

    lock_flag = threading.Event()
    fail_flag = threading.Event()
    thread1 = threading.Thread(target=try_to_lock, args=("key", lock_flag, fail_flag))
    thread1.daemon = True
    thread1.start()
    thread2 = threading.Thread(target=try_to_lock, args=("key", lock_flag, fail_flag))
    thread2.daemon = True
    thread2.start()
    lock_flag.wait(2.0)
    fail_flag.wait(2.0)
    thread1.join(1.0)
    thread2.join(1.0)
    assert lock_flag.is_set() and fail_flag.is_set()
