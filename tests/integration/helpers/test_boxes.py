import multiprocessing
import time

from edera.helpers import SharedBox


def test_shared_box_works_with_multiple_consumers():

    def produce():
        for i in range(1, 6):
            box.put(i)
            time.sleep(0.5)

    def consume(index):
        while box.get() != index:
            time.sleep(0.1)

    box = SharedBox()
    assert box.get() is None
    box.put(0)
    assert box.get() == 0
    producer = multiprocessing.Process(target=produce)
    consumers = [multiprocessing.Process(target=consume, args=(index,)) for index in range(1, 6)]
    for consumer in consumers:
        consumer.start()
    producer.start()
    for index, consumer in enumerate(consumers):
        consumer.join(index + 1)
        assert not consumer.is_alive()
    producer.join(1)
    assert not producer.is_alive()
