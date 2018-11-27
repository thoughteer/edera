import abc

import pytest
import six

from edera.helpers import Factory


def test_factory_works_correctly():

    @six.add_metaclass(abc.ABCMeta)
    class Object(object):

        @abc.abstractmethod
        def show(self):
            pass

    class InvalidFactory(Factory[Object]):

        def snow(self):
            return "sNow?"

    class ValidFactory(Factory[Object]):

        def show(self):
            return "cargo: %s" % str(self.cargo)

    with pytest.raises(TypeError):
        InvalidFactory[1, 2, 3]()
    assert ValidFactory[1]().show() == "cargo: 1"
    assert ValidFactory[1, 2, 3]().show() == "cargo: (1, 2, 3)"
