import abc

import six


@six.add_metaclass(abc.ABCMeta)
class Flag(object):
    """
    An interface for flags.

    A flag is a shared entity that can be raised and lowered by several users.
    Flags are initially lowered.

    Depending on implementation, users can concurrently operate the flag from different threads,
    processes, hosts, etc.

    Attributes:
        raised (Boolean) - whether the flag is raised
    """

    @abc.abstractmethod
    def down(self):
        """
        Lower the flag.
        """

    @abc.abstractproperty
    def raised(self):
        pass

    @abc.abstractmethod
    def up(self):
        """
        Raise the flag.
        """
