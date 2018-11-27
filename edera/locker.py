import abc

import six


@six.add_metaclass(abc.ABCMeta)
class Locker(object):
    """
    An interface for lockers.

    A locker is essentially a non-blocking mutex factory.
    You specify a key and get a key-specific lock object, which works as a context manager.

    No two clients at a time can acquire a lock for the same key. The notion of "client"
    depends on the scope of the locker: process, host, cluster, etc.
    """

    @abc.abstractmethod
    def lock(self, key, callback=None):
        """
        Create a lock object for the given key.

        Args:
            key (String) - a key to get a lock for
            callback (Optional[Callable[[], Any]]) - a function to call if the lock is lost
                Not all implementations will notify you about the loss.

        Returns:
            ContextManager - the lock object

        Raises:
            LockAcquisitionError if the lock has been already acquired
        """
