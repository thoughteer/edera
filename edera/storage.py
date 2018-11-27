import abc

import six


@six.add_metaclass(abc.ABCMeta)
class Storage(object):
    """
    An interface for storages.

    A storage is something that stores key-value pairs versioned chronologically.
    Both keys and values are strings, versions are integer numbers.
    Versions are not globally unique.

    Storages help to organize any stateful activities, such as caching and monitoring.
    """

    @abc.abstractmethod
    def clear(self):
        """
        Clear the storage.

        Raises:
            StorageOperationError if something went wrong
        """

    @abc.abstractmethod
    def delete(self, key, till=None):
        """
        Delete all data from the storage with the given key till the given version.

        Args:
            key (String) - a key to delete data for
            till (Optional[Integer]) - a maximum version for the records to delete (excluding)
                Default is $None - all versions will be deleted.

        Raises:
            StorageOperationError if something went wrong
        """

    @abc.abstractmethod
    def gather(self):
        """
        Fetch all data available in the storage.

        Returns:
            List[Tuple[String, Integer, String]] - (key, version, value) tuples

        Raises:
            StorageOperationError if something went wrong
        """

    @abc.abstractmethod
    def get(self, key, since=None, limit=None):
        """
        Select several latest records for the given key since the specified version.

        Args:
            key (String) - a key to select records for
            since (Optional[Integer]) - a version to start with (including)
                Default is $None - get all versions.
            limit (Optional[Integer]) - a maximum number of records to select
                Default is $None - as many as possible.

        Returns:
            List[Tuple[Integer, String]] - (version, value) tuples ordered by version
                Latest records go first.

        Raises:
            StorageOperationError if something went wrong
        """

    @abc.abstractmethod
    def put(self, key, value):
        """
        Store a key-value pair in the storage.

        Args:
            key (String) - a key
            value (String) - a value

        Returns:
            Integer - the generated version (increments over time)

        Raises:
            StorageOperationError if something went wrong
        """
