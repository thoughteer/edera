import collections
import contextlib
import os
import random
import sqlite3
import time
import threading

from edera.exceptions import StorageOperationError
from edera.storage import Storage


class SQLiteStorage(Storage):
    """
    An SQLite-based storage.

    It uses an SQLite table to store versioned key-value pairs.
    Notice that the storage will "own" the table, meaning, it may drop and re-create it.

    This implementation is fork- and thread-safe.
    However, not very efficient if you have too many operating clients (due to DB locking).

    Attributes:
        database (String) - the path to the database
        table (String) - the name of the table within the database
    """

    def __init__(self, database, table="master"):
        """
        Args:
            database (String) - a path to an SQLite database
            table (Optional[String]) - a table name
                Default is "master".
        """
        self.database = database
        self.table = table
        self.__local = collections.defaultdict(threading.local)
        self.__lock = threading.Lock()

    def clear(self):
        query = "DELETE FROM %s" % self.table
        with self.__connect() as cursor:
            cursor.execute(query)
            cursor.connection.isolation_level = None  # this is a workaround for Python 3.6
            cursor.execute("VACUUM")
            cursor.connection.isolation_level = ""

    def delete(self, key, till=None):
        query = "DELETE FROM %s WHERE key = ?" % self.table
        arguments = (key,)
        if till is not None:
            query += " AND version < ?"
            arguments += (till,)
        with self.__connect() as cursor:
            cursor.execute(query, arguments)
            cursor.connection.isolation_level = None  # this is a workaround for Python 3.6
            cursor.execute("VACUUM")
            cursor.connection.isolation_level = ""

    def gather(self):
        query = "SELECT key, version, value FROM %s" % self.table
        with self.__connect() as cursor:
            return cursor.execute(query).fetchall()

    def get(self, key, since=None, limit=None):
        query = "SELECT version, value FROM %s WHERE key = ?" % self.table
        arguments = (key,)
        if since is not None:
            query += " AND version >= ?"
            arguments += (since,)
        query += " ORDER BY version DESC"
        if limit is not None:
            query += " LIMIT %d" % limit
        with self.__connect() as cursor:
            return cursor.execute(query, arguments).fetchall()

    def put(self, key, value):
        query = "INSERT INTO %s (key, value) VALUES (?, ?)" % self.table
        arguments = (key, value)
        with self.__connect() as cursor:
            cursor.execute(query, arguments)
            return cursor.lastrowid

    @contextlib.contextmanager
    def __connect(self):
        pid = os.getpid()
        if not hasattr(self.__local[pid], "connection"):
            with self.__lock:  # seems like setting up WAL from multiple threads is not a good idea
                try:
                    connection = sqlite3.connect(self.database, detect_types=True)
                    self.__initialize(connection)
                except sqlite3.Error as error:
                    raise StorageOperationError(
                        "failed to connect to %r: %s" % (self.database, error))
                self.__local[pid].connection = connection
        connection = self.__local[pid].connection
        try:
            yield connection.cursor()
        except sqlite3.Error as error:
            raise StorageOperationError("failed to execute a query: %s" % error)
        try:
            connection.commit()
        except sqlite3.Error as error:
            raise StorageOperationError("failed to commit: %s" % error)

    def __initialize(self, connection):
        time.sleep(random.random())  # this is a workaround for Mac OS X (gets deadlocked)
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
        connection.commit()  # commit pragma statements before heavy operations
        connection.execute(
            "CREATE TABLE IF NOT EXISTS %s (key TEXT, version INTEGER PRIMARY KEY, value TEXT)"
            % self.table)
        connection.execute(
            "CREATE INDEX IF NOT EXISTS %s ON %s (key, version)"
            % (self.table + "__index", self.table))
        connection.commit()
        connection.text_factory = str
