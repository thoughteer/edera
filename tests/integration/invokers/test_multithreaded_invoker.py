import datetime
import threading
import time

import pytest

from edera.exceptions import ExcusableError
from edera.exceptions import ExcusableMasterSlaveInvocationError
from edera.exceptions import MasterSlaveInvocationError
from edera.invokers import MultiThreadedInvoker
from edera.routine import routine


def test_invoker_runs_actions_in_parallel():

    def add_index(index):
        collection.add(index)

    collection = set()
    actions = {
        "A": lambda: add_index(2),
        "B": lambda: add_index(1),
        "C": lambda: add_index(0),
    }
    MultiThreadedInvoker(actions).invoke()
    assert collection == {0, 1, 2}


def test_invoker_notifies_about_stops():

    def add_index(index):
        if index % 2 == 0:
            raise ExcusableError("index must be odd")
        collection.add(index)

    collection = set()
    actions = {
        "A": lambda: add_index(3),
        "B": lambda: add_index(2),
        "C": lambda: add_index(1),
        "D": lambda: add_index(0),
    }
    with pytest.raises(ExcusableMasterSlaveInvocationError) as info:
        MultiThreadedInvoker(actions).invoke()
    assert len(list(info.value.stopped_slaves)) == 2
    assert collection == {1, 3}


def test_invoker_notifies_about_failures():

    def add_index(index):
        if index % 2 == 0:
            raise RuntimeError("index must be odd")
        collection.add(index)

    collection = set()
    actions = {
        "A": lambda: add_index(3),
        "B": lambda: add_index(2),
        "C": lambda: add_index(1),
        "D": lambda: add_index(0),
    }
    with pytest.raises(MasterSlaveInvocationError) as info:
        MultiThreadedInvoker(actions).invoke()
    assert len(list(info.value.failed_slaves)) == 2
    assert collection == {1, 3}


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
            time.sleep(1.0)
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
            actions, interruption_timeout=datetime.timedelta(seconds=3.0)).invoke[interrupt]()
    assert time.time() - start_time < 6.0


def test_invoker_kills_hanging_slaves():

    def hang():
        while True:
            time.sleep(1.0)

    def interrupt():
        raise RuntimeError

    actions = {
        "A": hang,
        "B": hang,
    }
    with pytest.raises(RuntimeError):
        MultiThreadedInvoker(
            actions, interruption_timeout=datetime.timedelta(seconds=5.0)).invoke[interrupt]()
