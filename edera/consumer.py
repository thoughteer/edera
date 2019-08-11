import abc

import six


@six.add_metaclass(abc.ABCMeta)
class Consumer(object):
    """
    A generic consumer protocol.

    You can push elements to the consumer.
    It's up to the consumer how to treat the elements.
    """

    @abc.abstractmethod
    def push(self, element):
        """
        Push the element to the consumer.

        Args:
            element (Any)

        Raises:
            ConsumptionError if the consumer failed to accept the element
        """
