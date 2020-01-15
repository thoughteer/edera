import pytest

from edera.consumers import BasicConsumer
from edera.monitoring import MonitoringAgent
from edera.storages import InMemoryStorage


@pytest.fixture
def monitor():
    return InMemoryStorage()


@pytest.fixture
def consumer(monitor):
    return BasicConsumer(lambda kv: monitor.put(*kv))


@pytest.fixture
def agent(monitor, consumer):
    return MonitoringAgent("agent", monitor, consumer)
