import contextlib

import pytest

from edera.managers import CascadeManager


def test_cascade_works_with_empty_manager_list():
    with CascadeManager([]):
        pass


def test_cascade_enters_and_exits_all_managers():

    @contextlib.contextmanager
    def increment_and_decrement():
        counter[0] += 1
        try:
            yield
        finally:
            counter[0] -= 1

    counter = [0]
    with CascadeManager([increment_and_decrement() for _ in range(10)]):
        assert counter[0] == 10
    assert counter[0] == 0


def test_cascade_exits_already_entered_managers_if_one_fails():

    @contextlib.contextmanager
    def increment_and_decrement_but_fail_if_5():
        if counter[0] == 5:
            raise RuntimeError
        counter[0] += 1
        try:
            yield
        finally:
            counter[0] -= 1

    counter = [0]
    with pytest.raises(RuntimeError):
        with CascadeManager([increment_and_decrement_but_fail_if_5() for _ in range(10)]):
            assert False
    assert counter[0] == 0
