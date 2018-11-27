import abc

import six


@six.add_metaclass(abc.ABCMeta)
class Box(object):
    """
    An interface for primitive containers that store some value.

    A box is initially empty (contains $None).

    See also:
        $MultiBox
        $SharedBox
        $SimpleBox
    """

    @abc.abstractmethod
    def get(self):
        """
        Get the stored value.

        Returns:
            Any
        """

    @abc.abstractmethod
    def put(self, value):
        """
        Put the value into the box.

        Args:
            value (Any)
        """
