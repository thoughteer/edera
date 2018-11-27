import abc

import six


@six.add_metaclass(abc.ABCMeta)
class Worker(object):
    """
    An interface for a worker.

    A worker is a named unit that performs some action.
    It can run in a separate thread, process, or even host.

    The action should raise $SystemExit to terminate the worker intentionally.
    The worker stops if the action raises $ExcusableError.
    The worker fails if the action raises any other exception.

    Attributes:
        alive (Boolean) - whether the worker is still working
        failed (Boolean) - whether the worker has failed
        stopped (Boolean) - whether the worker has stopped
    """

    @abc.abstractmethod
    def __init__(self, name, action):
        """
        Args:
            name (String) - a name for the worker
            action (Callable[[], Any]) - an action function to invoke
        """

    @abc.abstractproperty
    def alive(self):
        pass

    @abc.abstractproperty
    def failed(self):
        pass

    @abc.abstractmethod
    def join(self, timeout):
        """
        Wait for the worker to finish and clean after it.

        Args:
            timeout (TimeDelta) - a timeout for the operation

        Raises:
            AssertionError if the worker hasn't started yet
        """

    @abc.abstractmethod
    def kill(self):
        """
        Kill the worker.

        After this the worker becomes not alive.

        Raises:
            AssertionError if the worker hasn't started yet
        """

    @abc.abstractmethod
    def start(self):
        """
        Start the worker.

        After the start the worker becomes alive and control is returned back to the caller.

        Raises:
            AssertionError if the worker has already started
        """

    @abc.abstractproperty
    def stopped(self):
        pass
