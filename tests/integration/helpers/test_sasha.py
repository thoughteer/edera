import os
import signal
import threading

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
    receive_flag = threading.Event()
    with Sasha({signal.SIGUSR1: receive_flag.set}):
        os.kill(os.getpid(), signal.SIGUSR1)
        receive_flag.wait(9.0)
        assert receive_flag.is_set()
        receive_flag.clear()
        os.kill(os.getpid(), signal.SIGUSR1)
        receive_flag.wait(9.0)
        assert receive_flag.is_set()
