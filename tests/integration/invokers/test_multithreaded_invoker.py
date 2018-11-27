import datetime
import threading
import time

import pytest

from edera.exceptions import MasterSlaveInvocationError
from edera.invokers import MultiThreadedInvoker
from edera.routine import routine


def test_invoker_runs_actions_in_parallel():

    def append_index(index):
        time.sleep(0.1 * index)
        collection.append(index)

    collection = []
    actions = {
        "A": lambda: append_index(2),
        "B": lambda: append_index(1),
        "C": lambda: append_index(0),
    }
    MultiThreadedInvoker(actions).invoke()
    assert collection == [0, 1, 2]


def test_invoker_notifies_about_failures():

    def append_index(index):
        time.sleep(0.1 * index)
        if index % 2 == 0:
            raise RuntimeError("index must be odd")
        collection.append(index)

    collection = []
    actions = {
        "A": lambda: append_index(3),
        "B": lambda: append_index(2),
        "C": lambda: append_index(1),
        "D": lambda: append_index(0),
    }
    with pytest.raises(MasterSlaveInvocationError) as info:
        MultiThreadedInvoker(actions).invoke()
    assert len(list(info.value.failed_slaves)) == 2
    assert collection == [1, 3]


def test_invoker_can_replicate_single_action():

    def increment():
        with mutex:
            counter[0] += 1
            if counter[0] == 15:
                raise RuntimeError("reached the end")

    mutex = threading.Lock()
    counter = [0]
    with pytest.raises(MasterSlaveInvocationError) as info:
        MultiThreadedInvoker.replicate(increment, count=15, prefix="T").invoke()
    assert len(list(info.value.failed_slaves)) == 1
    assert counter == [15]


def test_invoker_interrupts_slaves_after_being_interrupted():

    @routine
    def wait():
        while True:
            time.sleep(1)
            yield

    def interrupt():
        raise RuntimeError

    actions = {
        "A": wait,
        "B": wait,
    }
    start_time = time.time()
    with pytest.raises(RuntimeError):
        MultiThreadedInvoker(
            actions, interruption_timeout=datetime.timedelta(seconds=5)).invoke[interrupt]()
    assert time.time() - start_time < 3


def test_invoker_kills_hanging_slaves():

    def hang():
        while True:
            time.sleep(1)

    def interrupt():
        raise RuntimeError

    actions = {
        "A": hang,
        "B": hang,
    }
    with pytest.raises(RuntimeError):
        MultiThreadedInvoker(
            actions, interruption_timeout=datetime.timedelta(seconds=5)).invoke[interrupt]()