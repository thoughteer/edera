import abc

import six


@six.add_metaclass(abc.ABCMeta)
class Consumer(object):
    """
    A generic consumer protocol.

    You can feed elements to the consumer.
    It's up to the consumer how to treat the elements.
    """

    @abc.abstractmethod
    def consume(self, element):
        """
        Consume the element.

        Args:
            element (Any)

        Raises:
            ConsumptionError if the consumer failed to consume the element
        """
