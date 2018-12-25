import multiprocessing
import time

from edera.helpers import SharedBox


def test_shared_box_works_with_multiple_consumers():

    def produce():
        for i in range(1, 6):
            box.put(i)
            while box.get() is not None:
                time.sleep(1.0)

    def consume(index):
        while box.get() != index:
            time.sleep(0.2)
        box.put(None)

    box = SharedBox()
    assert box.get() is None
    box.put(0)
    assert box.get() == 0
    box.put(None)
    producer = multiprocessing.Process(target=produce)
    consumers = [multiprocessing.Process(target=consume, args=(index,)) for index in range(1, 6)]
    for consumer in consumers:
        consumer.daemon = True
        consumer.start()
    producer.daemon = True
    producer.start()
    for consumer in consumers:
        consumer.join(12.0)
        assert not consumer.is_alive()
    producer.join(6.0)
    assert not producer.is_alive()
