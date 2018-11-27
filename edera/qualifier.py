import abc

import six


@six.add_metaclass(abc.ABCMeta)
class Qualifier(object):
    """
    An interface for qualifiers.

    Qualifiers specialize on checking if a particular value meets certain criteria
    and converting it to its canonical form.
    For instance, one can check if some value is iterable and convert it to a list.
    They also represent such values as ASCII strings in platform-independent fashion.

    See also:
        $Parameter
    """

    @abc.abstractmethod
    def qualify(self, value):
        """
        Qualify the given value.

        Args:
            value (Any) - a value to check and convert

        Returns:
            Tuple[Any, String] - the canonical form of the value and its representation
                The representation must allow to distinguish different values.

        Raises:
            ValueQualificationError if the value doesn't suit
        """
