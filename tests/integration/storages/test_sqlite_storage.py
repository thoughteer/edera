import os
import os.path
import sqlite3
import stat

import pytest

from edera.exceptions import StorageOperationError
from edera.storages import SQLiteStorage


def test_storage_reports_about_connection_failures(tmpdir):
    os.chmod(str(tmpdir), stat.S_IREAD)
    with pytest.raises(StorageOperationError):
        SQLiteStorage(str(tmpdir.join("storage.db"))).get("key")


def test_storage_reports_about_execution_failures(sqlite_storage):
    sqlite_storage.put("key", "value")
    with sqlite3.connect(sqlite_storage.database) as connection:
        connection.execute("DROP TABLE %s" % sqlite_storage.table)
    with pytest.raises(StorageOperationError):
        sqlite_storage.put("another key", "another value")
