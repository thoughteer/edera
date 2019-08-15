import pytest

from edera.helpers import MultiBox
from edera.helpers import Proxy
from edera.helpers import SimpleBox


def test_proxy_delays_instantiation_and_delegates_access_correctly():
    box = SimpleBox()
    proxy = Proxy(box, list, [1, 2, 3])
    assert box.get() is None
    assert repr(proxy) == "[1, 2, 3]"
    assert box.get() == [1, 2, 3]
    assert proxy.__class__ is list
    proxy.extend([4, "5"])
    assert proxy == [1, 2, 3, 4, "5"]
    assert len(proxy) == 5
    assert proxy[0] == 1
    proxy[-1] = 5
    assert proxy[-1] == 5


def test_proxy_does_not_add_missing_special_methods():
    box = SimpleBox()
    proxy = Proxy(box, int, 6)
    with pytest.raises(TypeError):
        proxy[0]


def test_proxy_reinstantiates_subject_when_needed():

    class Object(object):

        counter = 0

        def __init__(self):
            Object.counter += 1

    box = SimpleBox()
    proxy = Proxy(box, Object)
    assert proxy.counter == 1
    assert proxy.counter == 1
    box.put(None)
    assert proxy.counter == 2


def test_proxy_can_proxy_proxies_to_builtin_derivatives():

    class T(tuple):
        def __new__(cls):
            return ()

    class P(T):
        def __new__(cls):
            return Proxy(SimpleBox(), T)

    assert len(Proxy(SimpleBox(), P)) == 0


def test_proxy_uses_correct_new_method_to_create_itself():

    class A(list):

        def __new__(cls):
            counter[0] += 1
            return [1, 2, 3]

    class B(A):

        def __new__(cls):
            return Proxy(SimpleBox(), A)

    class C(B):

        def __new__(cls):
            return Proxy(MultiBox(lambda: dispatcher.get()), B)

    counter = [0]
    dispatcher = SimpleBox()
    c = C()
    dispatcher.put(1)
    assert len(c) == 3
    assert counter[0] == 1
    dispatcher.put(2)
    assert len(c) == 3
    assert counter[0] == 2
    dispatcher.put(1)
    assert len(c) == 3
    assert counter[0] == 2
