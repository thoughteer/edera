import pytest

from edera.consumers import BasicConsumer
from edera.exceptions import ConsumptionError


def test_consumer_handles_elements_correctly():
    collector = []
    consumer = BasicConsumer(collector.append)
    consumer.consume(1)
    consumer.consume(2)
    consumer.consume(3)
    assert collector == [1, 2, 3]


def test_consumer_wraps_errors():
    consumer = BasicConsumer(lambda: 1 / 0)
    with pytest.raises(ConsumptionError):
        consumer.consume(0)
