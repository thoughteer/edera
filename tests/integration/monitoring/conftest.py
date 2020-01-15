import datetime

import pytest

import edera.helpers

from edera import routine
from edera import Timer
from edera.consumers import BasicConsumer
from edera.exceptions import StorageOperationError
from edera.invokers import MultiThreadedInvoker
from edera.monitoring import MonitoringAgent
from edera.monitoring import MonitoringUI
from edera.monitoring import MonitorWatcher
from edera.monitoring.snapshot import TaskLogUpdate
from edera.monitoring.snapshot import TaskStatusUpdate
from edera.monitoring.snapshot import WorkflowUpdate
from edera.storages import InMemoryStorage


@pytest.fixture
def monitor():
    return InMemoryStorage()


@pytest.fixture
def consumer(monitor):
    return BasicConsumer(lambda kv: monitor.put(*kv))


@pytest.fixture
def agent(monitor, consumer):
    result = MonitoringAgent("agent", monitor, consumer)
    result.register()
    result.push(WorkflowUpdate({"X": {"O"}, "Y": {"O"}, "O": set()}, {"X"}, {}))
    timestamp = edera.helpers.now()
    result.push(TaskStatusUpdate("O", "running", timestamp))
    result.push(TaskLogUpdate("O", "https://example.com", timestamp))
    result.push(TaskStatusUpdate("O", "completed", timestamp + datetime.timedelta(days=1, hours=2, minutes=3, seconds=4)))
    return result


@pytest.fixture
def watcher(monitor, agent):

    @routine
    def watch():
        yield result.run.defer(delay=datetime.timedelta(milliseconds=10))

    result = MonitorWatcher(monitor)
    timer = Timer(datetime.timedelta(milliseconds=200))
    try:
        MultiThreadedInvoker({"w": watch}).invoke[timer]()
    except Timer.Timeout:
        pass
    return result


@pytest.fixture
def broken_watcher(mocker, watcher):
    mocker.patch.object(MonitoringAgent, "pull", side_effect=StorageOperationError)
    return watcher


@pytest.yield_fixture
def ui(watcher):
    application = MonitoringUI("caption", watcher)
    with application.test_client() as result:
        yield result


@pytest.fixture
def void_ui():
    monitor = InMemoryStorage()
    watcher = MonitorWatcher(monitor)
    application = MonitoringUI("caption", watcher)
    with application.test_client() as result:
        yield result
