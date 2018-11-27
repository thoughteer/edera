import abc

import six


@six.add_metaclass(abc.ABCMeta)
class Invoker(object):
    """
    An interface for invokers.

    An invoker is just a callable object.
    When you call an invoker, it invokes something.
    For instance, it can call a function or other invokers in a special manner.
    """

    @abc.abstractmethod
    def invoke(self):
        """
        Invoke something.

        Returns:
            Any

        Raises:
            ExcusableInvocationError if something went wrong
            InvocationError if something went surprisingly wrong
        """
