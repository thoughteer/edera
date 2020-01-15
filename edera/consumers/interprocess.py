import logging
import multiprocessing

import edera.helpers

from edera.consumer import Consumer
from edera.exceptions import ConsumptionError
from edera.routine import deferrable
from edera.routine import routine


class InterProcessConsumer(Consumer):
    """
    An inter-process consumer that buffers elements in a queue.

    In order to start handling buffered elements you need to call $run.

    Attributes:
        handler (Callable[[Any], Any]) - the handler called for every element
        capacity (Integer) - the limit on the number of pending elements in the queue
        backoff (TimeDelta) - the delay after each handling failure
    """

    def __init__(self, handler, capacity, backoff):
        """
        Args:
            handler (Callable[[Any], Any]) - a handler to call for every element
            capacity (Integer) - a limit on the number of pending elements in the queue
            backoff (TimeDelta) - a delay after each handling failure
        """
        self.handler = handler
        self.capacity = capacity
        self.backoff = backoff
        self.__fifo = multiprocessing.Queue(capacity)

    def consume(self, element):
        try:
            self.__fifo.put(element, False)
        except Exception:
            raise ConsumptionError("FIFO is full")

    @routine
    def run(self):
        """
        Run an infinite consumption loop.

        Ignores all errors that occur in the handler, but logs them at the INFO level.
        """
        element = Void
        while True:
            if element is Void:
                try:
                    element = self.__fifo.get(False)
                except Exception:
                    yield edera.helpers.sleep.defer(self.backoff)
                    continue
            try:
                yield deferrable(self.handler).defer(element)
            except Exception as error:
                logging.getLogger(__name__).info("Failed to handle %r: %s", element, error)
                yield edera.helpers.sleep.defer(self.backoff)
            else:
                element = Void
                yield


class Void(object):
    pass
