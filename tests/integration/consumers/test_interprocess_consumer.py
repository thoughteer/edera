import datetime
import multiprocessing

import pytest

from edera import Timer
from edera.consumers import InterProcessConsumer
from edera.exceptions import ConsumptionError
from edera.invokers import MultiProcessInvoker


def test_consumer_limits_its_capacity():
    consumer = InterProcessConsumer(lambda element: None, 3, datetime.timedelta(seconds=0))
    consumer.consume(1)
    consumer.consume(2)
    consumer.consume(3)
    with pytest.raises(ConsumptionError):
        consumer.consume(0)


def test_consumer_handles_elements_correctly():

    def consume():
        for element in range(1, 4):
            consumer.consume(element)

    def handle(element):
        result.put(element)

    consumer = InterProcessConsumer(handle, 3, datetime.timedelta(seconds=0.1))
    result = multiprocessing.Queue()
    invoker = MultiProcessInvoker({"c": consume, "r": consumer.run})
    try:
        invoker.invoke[Timer(datetime.timedelta(seconds=10))]()
    except Timer.Timeout:
        pass
    assert [result.get(timeout=1.0) for _ in range(3)] == [1, 2, 3]


def test_consumer_handles_errors_silently():

    def consume():
        for element in range(1, 4):
            consumer.consume(element)

    def handle(element):
        result.put(element)
        1 / 0  # should be ignored

    consumer = InterProcessConsumer(handle, 3, datetime.timedelta(seconds=0.1))
    result = multiprocessing.Queue()
    invoker = MultiProcessInvoker({"c": consume, "r": consumer.run})
    try:
        invoker.invoke[Timer(datetime.timedelta(seconds=10))]()
    except Timer.Timeout:
        pass
    assert [result.get(timeout=1.0) for _ in range(3)] == [1, 1, 1]
