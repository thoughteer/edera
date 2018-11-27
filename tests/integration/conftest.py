import os

import kazoo.client
import pymongo
import pytest

from edera.helpers import Lazy


@pytest.fixture(scope="session")
def zookeeper_service():
    client = kazoo.client.KazooClient(hosts=os.environ["EDERA_ZOOKEEPER_HOSTS"])
    if not client.start_async().wait(timeout=3):
        pytest.skip("ZooKeeper is unavailable")
    client.stop()
    client.close()


@pytest.yield_fixture
def zookeeper(zookeeper_service):
    client = kazoo.client.KazooClient(hosts=os.environ["EDERA_ZOOKEEPER_HOSTS"])
    client.start()
    try:
        yield client
    finally:
        client.stop()
        client.close()


@pytest.fixture(scope="session")
def mongodb_service():
    client = pymongo.MongoClient(os.environ["EDERA_MONGODB_URI"], serverselectiontimeoutms=3000)
    try:
        client.admin.command('ismaster')
    except pymongo.errors.ConnectionFailure:
        pytest.skip("MongoDB is unavailable")
    client.close()
    del client


@pytest.yield_fixture
def mongo(mongodb_service):
    client = Lazy[pymongo.MongoClient](os.environ["EDERA_MONGODB_URI"])
    try:
        yield client
    finally:
        client.instance.close()
        client.destroy()
