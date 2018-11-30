import uuid

import pytest

from edera.lockers import DirectoryLocker
from edera.lockers import ProcessLocker
from edera.lockers import ZooKeeperLocker


@pytest.fixture
def process_locker():
    return ProcessLocker()


@pytest.fixture
def directory_locker(debugger, tmpdir):
    return DirectoryLocker(str(tmpdir))


@pytest.yield_fixture
def zookeeper_locker(debugger, zookeeper):
    znode = "/" + uuid.uuid4().hex
    try:
        yield ZooKeeperLocker(zookeeper, znode)
    finally:
        zookeeper.start()
        zookeeper.delete(znode, recursive=True)


@pytest.fixture(params=["process_locker", "directory_locker", "zookeeper_locker"])
def locker(request):
    return request.getfixturevalue(request.param)


@pytest.fixture(params=["process_locker", "directory_locker", "zookeeper_locker"])
def multithreaded_locker(request):
    return request.getfixturevalue(request.param)
