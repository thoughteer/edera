import os.path
import uuid

import pytest

from edera.storages import InMemoryStorage
from edera.storages import MongoStorage
from edera.storages import SQLiteStorage


@pytest.fixture
def inmemory_storage():
    return InMemoryStorage()


@pytest.fixture
def sqlite_database(tmpdir):
    return os.path.join(str(tmpdir), "storage.db")


@pytest.fixture
def sqlite_storage(sqlite_database):
    return SQLiteStorage(sqlite_database)


@pytest.yield_fixture
def mongo_database(mongo):
    name = uuid.uuid4().hex
    try:
        yield name
    finally:
        mongo.instance.drop_database(name)


@pytest.fixture
def mongo_storage(mongo, mongo_database):
    return MongoStorage(mongo, mongo_database, "storage")


@pytest.fixture(params=["inmemory_storage", "sqlite_storage", "mongo_storage"])
def storage(request):
    return request.getfixturevalue(request.param)


@pytest.fixture(params=["inmemory_storage", "sqlite_storage", "mongo_storage"])
def multithreaded_storage(request):
    return request.getfixturevalue(request.param)


@pytest.fixture(params=["sqlite_storage", "mongo_storage"])
def multiprocess_storage(request):
    return request.getfixturevalue(request.param)
