import datetime

import pytest

import edera.helpers

from edera import deferrable
from edera import routine
from edera import Timer
from edera.routine import Routine


def test_routine_can_be_called_as_ordinary_function():

    @routine
    def mark():
        yield
        invoked[0] = True
        yield

    invoked = [False]
    mark()
    assert invoked[0]


def test_routine_can_yield_result():

    @routine
    def yield_result():
        yield
        yield "result"

    assert yield_result() == "result"


def test_routine_invokes_auditors_on_yield():

    @routine
    def step(count):
        for _ in range(count):
            yield

    def audit():
        counter[0] += 1

    counter = [0]
    step[audit](3)
    assert counter[0] == 3


def test_routine_calls_can_be_nested():

    @routine
    def step(count):
        for _ in range(count):
            yield

    @routine
    def overstep(count):
        for i in range(count):
            yield step.defer(i)

    def audit():
        counter[0] += 1

    counter = [0]
    overstep[audit](5)
    assert counter[0] == 15


def test_deferrable_handles_ordinary_functions_well():

    @deferrable
    def return_result():
        return "result"

    @routine
    def yield_result():
        result = yield return_result.defer()
        yield result

    assert yield_result() == "result"


def test_nested_routine_can_raise_exception():

    @deferrable
    def fail():
        raise RuntimeError("uh")

    class Nester(object):

        @routine
        def nest(self):
            for i in range(5):
                try:
                    if i % 2 == 0:
                        yield fail.defer()
                    else:
                        yield
                except RuntimeError:
                    counter[0] += 1

    counter = [0]
    Nester().nest()
    assert counter[0] == 3


def test_routine_auditors_can_be_added_on_fly():

    @routine
    def step(count):
        for _ in range(count):
            yield

    @routine
    def overstep(count):
        for i in range(count):
            yield step[audit_further].defer(i)

    def audit():
        counter[0] += 1

    def audit_further():
        counter[0] -= 2

    counter = [0]
    overstep[audit](5)
    assert counter[0] == -5


def test_routine_auditors_can_raise_exception():

    @routine
    def swallow():
        try:
            yield
        except RuntimeError:
            assert False

    def audit():
        raise RuntimeError

    with pytest.raises(RuntimeError):
        swallow[audit]()


def test_routine_can_fix_some_arguments():

    @routine
    def add(x, y, z):
        yield x + y + z

    increment = add.fix(0, z=1)
    assert isinstance(increment, Routine)
    assert increment(y=2) == 3
    assert increment(2) == 3


def test_routine_timer_works_correctly():
    timer = Timer(datetime.timedelta(seconds=1))
    with pytest.raises(Timer.Timeout):
        edera.helpers.sleep[timer](datetime.timedelta(seconds=5))
