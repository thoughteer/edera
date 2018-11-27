import contextlib
import errno
import logging
import os
import os.path
import sqlite3

import edera.helpers

from edera.exceptions import LockAcquisitionError
from edera.locker import Locker


class DirectoryLocker(Locker):
    """
    A directory-level locker.

    A directory-level lock works as an inter-process mutex.
    It creates a temporary SQLite3 database and locks it using "BEGIN EXCLUSIVE".
    It is a good practice to use a temporary directory for them (like /tmp).
    Once the owning process dies, the lock is automatically released.

    Don't forget to clean the directory from time to time!

    Attributes:
        path (String) - the directory path (absolute)
    """

    def __init__(self, path):
        """
        Args:
            path (String) - a base path for lock files

        The base path will be created if doesn't exist.
        """
        self.path = os.path.abspath(path)

    def __repr__(self):
        return "<%s: path %r>" % (self.__class__.__name__, self.path)

    @contextlib.contextmanager
    def lock(self, key, callback=None):
        try:
            os.makedirs(self.path)
        except OSError as error:
            if error.errno == errno.EEXIST and os.path.isdir(self.path):
                pass
            else:
                raise
        lock_file_path = os.path.join(self.path, edera.helpers.sha1(key))
        logging.getLogger(__name__).debug("Lock file: %s", lock_file_path)
        try:
            connection = sqlite3.connect(lock_file_path, timeout=0.2)
            connection.execute("BEGIN EXCLUSIVE").fetchone()
        except sqlite3.OperationalError:
            raise LockAcquisitionError(key)
        try:
            yield
        finally:
            try:
                os.remove(lock_file_path)
            except OSError:
                pass
            if connection is not None:
                connection.close()
