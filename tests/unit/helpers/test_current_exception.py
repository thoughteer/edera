import pytest

from edera.helpers import CurrentException


def test_current_exception_works_correctly():
    with pytest.raises(ZeroDivisionError):
        try:
            1 / 0
        except ZeroDivisionError:
            error = CurrentException()
            try:
                {"one": 1}["two"]
            except KeyError:
                pass
            error.reraise()
