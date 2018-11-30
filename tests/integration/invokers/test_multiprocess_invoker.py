import datetime
import multiprocessing
import time

import pytest

from edera.exceptions import MasterSlaveInvocationError
from edera.invokers import MultiProcessInvoker
from edera.routine import routine


def test_invoker_runs_actions_in_parallel():

    def append_index(index):
        time.sleep(0.1 * index)
        collection.put(index)

    collection = multiprocessing.Queue()
    actions = {
        "A": lambda: append_index(2),
        "B": lambda: append_index(1),
        "C": lambda: append_index(0),
    }
    MultiProcessInvoker(actions).invoke()
    assert [collection.get(timeout=1) for _ in range(3)] == [0, 1, 2]


def test_invoker_notifies_about_failures():

    def append_index(index):
        time.sleep(0.1 * index)
        if index % 2 == 0:
            raise RuntimeError("index must be odd")
        collection.put(index)

    collection = multiprocessing.Queue()
    actions = {
        "A": lambda: append_index(3),
        "B": lambda: append_index(2),
        "C": lambda: append_index(1),
        "D": lambda: append_index(0),
    }
    with pytest.raises(MasterSlaveInvocationError) as info:
        MultiProcessInvoker(actions).invoke()
    assert len(info.value.failed_slaves) == 2
    assert [collection.get(timeout=1) for _ in range(2)] == [1, 3]


def test_invoker_can_replicate_single_action():

    def increment():
        with mutex:
            counter.put(counter.get(timeout=1) + 1)

    mutex = multiprocessing.Lock()
    counter = multiprocessing.Queue()
    counter.put(0)
    MultiProcessInvoker.replicate(increment, count=15, prefix="P").invoke()
    assert counter.get(timeout=1) == 15


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
        MultiProcessInvoker(
            actions, interruption_timeout=datetime.timedelta(seconds=5)).invoke[interrupt]()
    assert time.time() - start_time < 3


def test_invoker_kills_hanging_slaves():

    def hang():
        while True:
            time.sleep(5)

    def interrupt():
        raise RuntimeError

    actions = {
        "A": hang,
        "B": hang,
    }
    with pytest.raises(RuntimeError):
        MultiProcessInvoker(
            actions, interruption_timeout=datetime.timedelta(seconds=1)).invoke[interrupt]()
