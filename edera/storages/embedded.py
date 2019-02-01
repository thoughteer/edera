import base64

from edera.storage import Storage


class EmbeddedStorage(Storage):
    """
    A storage within another storage.

    You can safely operate multiple embedded storages with different key-spaces within
    the same base storage.
    However, you cannot reliably operate the base storage itself at the same time.

    Example:
        >>> base = InMemoryStorage()
        >>> monitor = EmbeddedStorage(base, "monitor")
        >>> cache = EmbeddedStorage(base, "cache")
        >>> monitor.put("key", "value")
        >>> cache.get("key")
        []
    """

    def __init__(self, base, keyspace):
        """
        Args:
            base (Storage) - a base storage
            keyspace (String) - a key-space name (unique within the base storage)
        """
        self.__base = base
        self.__prefix = base64.b64encode(keyspace.encode("ASCII")).decode("ASCII") + ":"

    def delete(self, key, till=None):
        self.__base.delete(self.__prefix + key, till=till)

    def get(self, key, since=None, limit=None):
        return self.__base.get(self.__prefix + key, since=since, limit=limit)

    def put(self, key, value):
        return self.__base.put(self.__prefix + key, value)
