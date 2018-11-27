import collections
import threading

import six

from edera.storage import Storage


class InMemoryStorage(Storage):
    """
    A simple in-memory storage.

    This implementation is both thread-safe and fork-safe.
    """

    def __init__(self):
        self.__records = collections.defaultdict(list)
        self.__offsets = collections.defaultdict(int)
        self.__lock = threading.Lock()

    def clear(self):
        with self.__lock:
            self.__records.clear()
            self.__offsets.clear()

    def delete(self, key, till=None):
        with self.__lock:
            values = self.__records[key]
            count = len(values) if till is None else max(till - self.__offsets[key], 0)
            del values[:count]
            self.__offsets[key] += count

    def gather(self):
        with self.__lock:
            return [
                (key, index + self.__offsets[key], value)
                for key, values in six.iteritems(self.__records)
                for index, value in enumerate(values)
            ]

    def get(self, key, since=None, limit=None):
        with self.__lock:
            since = 0 if since is None else since - self.__offsets[key]
            values = self.__records[key]
            count = len(values)
            limit = count if limit is None else max(limit, 0)
            return [
                (index + self.__offsets[key], values[index])
                for index in range(count - 1, max(since, count - limit) - 1, -1)
            ]

    def put(self, key, value):
        with self.__lock:
            self.__records[key].append(value)
            return self.__offsets[key] + len(self.__records[key]) - 1
