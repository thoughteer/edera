import datetime
import multiprocessing

import pytest

from edera.consumers import InterProcessConsumer
from edera.exceptions import ConsumptionError
from edera.invokers import MultiProcessInvoker


def test_consumer_limits_its_capacity():
    consumer = InterProcessConsumer(lambda element: None, 3, datetime.timedelta(seconds=0))
    consumer.push(1)
    consumer.push(2)
    consumer.push(3)
    with pytest.raises(ConsumptionError):
        consumer.push(0)


def test_consumer_handles_elements_correctly():

    def push():
        for element in range(1, 4):
            consumer.push(element)

    def handle(element):
        result.put(element)

    def interrupt():
        if datetime.datetime.utcnow() > start_time + datetime.timedelta(seconds=5):
            raise SystemExit

    consumer = InterProcessConsumer(handle, 3, datetime.timedelta(seconds=0.1))
    result = multiprocessing.Queue()
    invoker = MultiProcessInvoker({"p": push, "c": consumer.consume})
    start_time = datetime.datetime.utcnow()
    try:
        invoker.invoke[interrupt]()
    except SystemExit:
        pass
    assert [result.get(timeout=1.0) for _ in range(3)] == [1, 2, 3]
