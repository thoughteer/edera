from edera.helpers import MultiBox
from edera.helpers import SimpleBox


def test_multibox_works_correctly():
    key = 1
    box = MultiBox(lambda: key)
    assert box.get() is None
    box.put(None)
    box.put(1)
    assert box.get() == 1
    key = 2
    assert box.get() is None
    box.put(2)
    assert box.get() == 2


def test_simple_box_works_correctly():
    box = SimpleBox()
    assert box.get() is None
    box.put(1)
    assert box.get() == 1
    box.put(2)
    assert box.get() == 2
