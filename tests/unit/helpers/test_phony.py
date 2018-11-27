from edera.helpers import Phony
from edera.helpers import phony


def test_phony_works_as_callable_singleton():
    assert Phony() is None
    assert Phony(2) is None
    assert Phony(2, test="test") is None


def test_phony_decorator_makes_everything_phony():

    @phony
    def square(x):
        return x**2

    assert square is Phony
