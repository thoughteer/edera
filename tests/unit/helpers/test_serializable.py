import abc

import six

import edera.helpers

from edera.helpers import AbstractSerializable
from edera.helpers import Serializable
from edera.helpers.serializable import BooleanField
from edera.helpers.serializable import DateTimeField
from edera.helpers.serializable import GenericField
from edera.helpers.serializable import IntegerField
from edera.helpers.serializable import ListField
from edera.helpers.serializable import MappingField
from edera.helpers.serializable import OptionalField
from edera.helpers.serializable import SetField
from edera.helpers.serializable import StringField
from edera.helpers.serializable import TupleField


class MicroObject(Serializable):

    z = BooleanField


class MacroObject(Serializable):

    a = DateTimeField
    b = GenericField(MicroObject)
    c = ListField(IntegerField)
    d = MappingField(StringField, IntegerField)
    e = OptionalField(IntegerField)
    f = SetField(IntegerField)
    g = StringField
    h = TupleField(IntegerField, StringField)


class AbstractObject(AbstractSerializable):

    x = StringField

    @abc.abstractmethod
    def idle(self):
        pass


class ConcreteObject(AbstractObject):

    y = StringField

    def idle(self):
        pass


def test_serializable_can_be_restored():
    o = MacroObject()
    o.a = edera.helpers.now()
    o.b = MicroObject()
    o.b.z = True
    o.c = [1, 2, 3]
    o.d = {"1": 1, "2": 2, "3": 3}
    o.e = None
    o.f = {1, 2, 3}
    o.g = "string"
    o.h = (0, "0")
    s = o.serialize()
    s.encode("ASCII")
    r = MacroObject.deserialize(s)
    assert r.a == o.a
    assert r.b.z == o.b.z
    assert r.c == o.c
    assert r.d == o.d
    assert r.e is None
    assert r.f == o.f
    assert r.g == o.g
    assert r.h == o.h


def test_abstract_serializable_can_be_restored():
    o = ConcreteObject()
    o.x = "x"
    o.y = "y"
    s = o.serialize()
    s.encode("ASCII")
    r = AbstractObject.deserialize(s)
    assert isinstance(r, ConcreteObject)
    assert r.x == o.x
    assert r.y == o.y
