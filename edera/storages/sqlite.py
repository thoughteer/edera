import collections
import contextlib
import os
import sqlite3
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

    def delete(self, key, till=None):
        query = "DELETE FROM %s WHERE key = ?" % self.table
        arguments = (key,)
        if till is not None:
            query += " AND version < ?"
            arguments += (till,)
        with self.__connect() as cursor:
            cursor.execute(query, arguments)
            cursor.connection.isolation_level = None  # prevent auto-commit
            cursor.execute("VACUUM")
            cursor.connection.isolation_level = ""

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
        with self.__lock:
            if not hasattr(self.__local[pid], "connection"):
                try:
                    connection = self.__create_connection()
                except sqlite3.Error as error:
                    raise StorageOperationError(
                        "failed to connect to %r: %s" % (self.database, error))
                self.__local[pid].connection = connection
        connection = self.__local[pid].connection
        try:
            with self.__use(connection) as cursor:
                yield cursor
        except sqlite3.Error as error:
            raise StorageOperationError("failed to execute a query: %s" % error)

    def __create_connection(self):
        result = sqlite3.connect(self.database, detect_types=True)
        with self.__use(result) as cursor:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS %s (key TEXT, version INTEGER PRIMARY KEY, value TEXT)"
                % self.table)
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS %s ON %s (key, version)"
                % (self.table + "__index", self.table))
        result.text_factory = lambda data: data.decode("ASCII")
        return result

    @contextlib.contextmanager
    def __use(self, connection):
        cursor = connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
        connection.commit()
