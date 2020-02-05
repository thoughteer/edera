import pytest

import edera.helpers

from edera.helpers import memoized


def test_functions_can_be_memoized():

    @memoized
    def fibonacci(n):
        fibonacci.calls += 1
        return 1 if n <= 2 else fibonacci(n - 1) + fibonacci(n - 2)

    fibonacci.calls = 0
    assert fibonacci(100) == 354224848179261915075
    assert fibonacci.calls == 100
    assert fibonacci(5) == 5
    assert fibonacci.calls == 100


def test_methods_can_be_memoized():

    class Fibonacci(object):

        def __init__(self):
            self.calls = 0

        @memoized
        def compute(self, n):
            self.calls += 1
            return 1 if n <= 2 else self.compute(n - 1) + self.compute(n - 2)

    assert Fibonacci.compute.__name__ == "compute"
    fibonacci = Fibonacci()
    assert fibonacci.compute(100) == 354224848179261915075
    assert fibonacci.calls == 100
    assert fibonacci.compute(5) == 5
    assert fibonacci.calls == 100
    assert Fibonacci().compute(5) == 5
    assert fibonacci.calls == 100


def test_now_returns_utc_time():
    assert edera.helpers.now().utcoffset().total_seconds() == 0


def test_mappings_get_rendered_correctly():
    value = {1: "1", 2: "2"}
    assert edera.helpers.render(value) == "\n * 1 => '1'\n * 2 => '2'"


def test_iterables_get_rendered_correctly():
    value = (["1"], ["2", "3"])
    assert edera.helpers.render(value) == "\n * ['1']\n * ['2', '3']"


def test_rendering_fails_if_not_supported():
    with pytest.raises(NotImplementedError):
        edera.helpers.render(1)


def test_sha1_produces_correct_result():
    assert edera.helpers.sha1("string") == "ecb252044b5ea0f679ee78ec1a12904739e2904d"


def test_string_squashing_works_correctly():
    assert list(edera.helpers.squash_strings([])) == []
    assert list(edera.helpers.squash_strings(["!@#"])) == ["!@#"]
    assert list(edera.helpers.squash_strings(["!@#a", "!@%a"])) == ["!@#a", "!@%a"]
    assert list(edera.helpers.squash_strings(["!@#a_b-c", "!@%x_y-z"])) == ["a_b-c", "x_y-z"]
    assert list(edera.helpers.squash_strings(["a", "a b", "b c"])) == ["a", "a\nb", "b"]
    assert list(edera.helpers.squash_strings(["a b c", "a b d"])) == ["a\nc", "a\nd"]
    assert list(edera.helpers.squash_strings(["a", "a b"])) == ["a", "a\nb"]
    with pytest.raises(AssertionError):
        list(edera.helpers.squash_strings(["a", "a"]))
    with pytest.raises(AssertionError):
        list(edera.helpers.squash_strings(["a", ""]))
