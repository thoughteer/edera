import multiprocessing
import os
import signal
import time

import pytest

from edera.helpers import Sasha


def test_sasha_can_be_entered_and_exited_normally():
    with Sasha({signal.SIGTERM: lambda: None}):
        pass


def test_sasha_still_works_with_no_handlers():
    with Sasha({}):
        pass


def test_sasha_is_not_reentrant():
    sasha = Sasha({signal.SIGTERM: lambda: None})
    with sasha:
        with pytest.raises(AssertionError):
            with sasha:
                pass


def test_sasha_restores_original_handlers_on_exit():
    original_handler = signal.getsignal(signal.SIGTERM)
    with Sasha({signal.SIGTERM: lambda: None}):
        pass
    assert signal.getsignal(signal.SIGTERM) is original_handler


def test_sasha_handles_signals_correctly():

    def target(ready_flag, receive_flag):
        with Sasha({signal.SIGINT: receive_flag.set, signal.SIGTERM: receive_flag.set}):
            ready_flag.set()
            while True:
                time.sleep(1.0)

    ready_flag = multiprocessing.Event()
    receive_flag = multiprocessing.Event()
    process = multiprocessing.Process(target=target, args=(ready_flag, receive_flag))
    process.daemon = True
    process.start()
    ready_flag.wait(1.0)
    os.kill(process.pid, signal.SIGINT)
    receive_flag.wait(1.0)
    assert receive_flag.is_set()
    receive_flag.clear()
    os.kill(process.pid, signal.SIGTERM)
    receive_flag.wait(1.0)
    assert receive_flag.is_set()
    receive_flag.clear()
    os.kill(process.pid, signal.SIGINT)
    receive_flag.wait(1.0)
    assert receive_flag.is_set()
    os.kill(process.pid, signal.SIGKILL)
    process.join()
