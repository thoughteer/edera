import abc

import six


@six.add_metaclass(abc.ABCMeta)
class Nameable(object):
    """
    An abstract base class for objects that have a unique name.

    All instances of $Nameable are hashable and comparable.
    They are supposed to be fully represented by their name.

    The simplest way to create a nameable object class is to subclass $Parameterizable.

    Attributes:
        name (String) - the unique name

    See also:
        $Parameterizable
    """

    def __eq__(self, other):
        assert other is None or isinstance(other, Nameable)
        return other is not None and other.name == self.name

    def __gt__(self, other):
        return other is None or self.name > other.name

    def __hash__(self):
        return hash(self.name)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.name

    @abc.abstractproperty
    def name(self):
        pass
