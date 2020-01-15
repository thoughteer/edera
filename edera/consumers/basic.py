from edera.consumer import Consumer
from edera.exceptions import ConsumptionError
from edera.routine import deferrable
from edera.routine import routine


class BasicConsumer(Consumer):
    """
    A basic consumer that simply applies a given function to each element.
    """

    def __init__(self, handler):
        """
        Args:
            handler (Callable[[Any], None]) - a function to be applied to each element
        """
        self.__handler = handler

    @routine
    def consume(self, element):
        try:
            yield deferrable(self.__handler).defer(element)
        except Exception as error:
            raise ConsumptionError("failed to handle %r: %s" % (element, error))
