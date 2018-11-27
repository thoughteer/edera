import pytest

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
