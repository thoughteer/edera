import logging
import multiprocessing

import edera.helpers

from edera.exceptions import ConsumptionError
from edera.routine import deferrable
from edera.routine import routine


class InterProcessConsumer(object):
    """
    An inter-process consumer that buffers elements in a queue.

    In order to start handling buffered elements you need to call $consume.

    Attributes:
        handler (Callable[[Any], Any]) - the handler called on every push
        capacity (Integer) - the limit on the number of pending elements in the queue
        backoff (TimeDelta) - the delay after each handling failure
    """

    def __init__(self, handler, capacity, backoff):
        """
        Args:
            handler (Callable[[Any], Any]) - a handler to call on every push
            capacity (Integer) - a limit on the number of pending elements in the queue
            backoff (TimeDelta) - a delay after each handling failure
        """
        self.handler = handler
        self.capacity = capacity
        self.backoff = backoff
        self.__fifo = multiprocessing.Queue(capacity)

    @routine
    def consume(self):
        """
        Run an infinite consumption loop.

        Ignores all errors that occur in the handler, but logs them at the DEBUG level.
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
                logging.getLogger(__name__).debug("Failed to handle %r: %s", element, error)
                yield edera.helpers.sleep.defer(self.backoff)
            else:
                element = Void
                yield

    def push(self, element):
        try:
            self.__fifo.put(element, False)
        except Exception:
            raise ConsumptionError("FIFO is full")


class Void(object):
    pass
