import pytest

from edera import Nameable


class Thing(Nameable):

    @property
    def name(self):
        return "thing"


class ThisThing(Nameable):

    @property
    def name(self):
        return "this thing"


class ThatThing(Nameable):

    @property
    def name(self):
        return "that thing"


def test_nameable_provides_access_to_its_name():
    assert Thing().name == "thing"


def test_nameable_can_be_compared_to_none():
    assert Thing() != None
    assert not Thing() == None


def test_nameables_with_same_name_are_equal():
    assert Thing() == Thing()
    assert not Thing() != Thing()


def test_nameables_with_different_names_are_not_equal():
    assert ThisThing() != ThatThing()
    assert not ThisThing() == ThatThing()


def test_nameables_can_form_sets():
    assert {ThisThing(), ThisThing(), ThatThing()} == {ThisThing(), ThatThing()}


def test_nameable_can_be_used_as_dictionary_key():
    dictionary = {
        ThisThing(): 1,
        ThatThing(): 2,
    }
    assert dictionary[ThisThing()] == 1
    assert dictionary[ThatThing()] == 2


def test_nameable_is_represented_by_its_name():
    assert repr(Thing()) == str(Thing()) == "thing"
