import pymongo
import pytest

from edera.exceptions import StorageOperationError
from edera.helpers import Lazy
from edera.storages import MongoStorage


def test_storage_reports_about_operation_failures():
    broken_mongo = Lazy[pymongo.MongoClient]("mongodb://watzub", serverselectiontimeoutms=10)
    broken_mongo_storage = MongoStorage(broken_mongo, "broken", "storage")
    with pytest.raises(StorageOperationError):
        broken_mongo_storage.delete("key")
    with pytest.raises(StorageOperationError):
        broken_mongo_storage.get("key")
    with pytest.raises(StorageOperationError):
        broken_mongo_storage.put("key", "value")
