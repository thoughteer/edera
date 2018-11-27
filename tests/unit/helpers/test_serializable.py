import six

from edera.helpers import Serializable


class Object(Serializable):

    def __init__(self, x):
        self.x = x

    @property
    def y(self):
        return self.x**2


def test_serializable_can_be_restored():
    serialization = Object(5).serialize()
    assert isinstance(serialization, six.string_types)
    assert Object.deserialize(serialization).y == 25
