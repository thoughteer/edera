import datetime
import logging

import edera.helpers

from edera.exceptions import ExcusableError
from edera.invoker import Invoker
from edera.routine import deferrable
from edera.routine import routine


class PersistentInvoker(Invoker):
    """
    An invoker that calls its action in an infinite loop.

    It ignores all $Exception's raised by the action.

    This invoker is interruptible.

    Attributes:
        action (Callable[[], Any]) - the action function
        delay (TimeDelta) - the minimum delay between consecutive action calls
    """

    def __init__(self, action, delay=datetime.timedelta(minutes=1)):
        """
        Args:
            action (Callable[[], Any]) - a function to call
            delay (TimeDelta) - a minimum delay between consecutive action calls
                Default is 1 minute.
        """
        self.action = action
        self.delay = delay

    @routine
    def invoke(self):
        try:
            while True:
                start_time = datetime.datetime.utcnow()
                try:
                    yield deferrable(self.action).defer()
                except ExcusableError as error:
                    logging.getLogger(__name__).info("Attempt stopped: %s", error)
                except Exception:
                    logging.getLogger(__name__).exception("Attempt failed:")
                elapsed_time = datetime.datetime.utcnow() - start_time
                sleep_time = max(self.delay - elapsed_time, datetime.timedelta())
                logging.getLogger(__name__).debug("Next attempt in %s", sleep_time)
                yield edera.helpers.sleep.defer(sleep_time)
        except BaseException as error:
            logging.getLogger(__name__).debug("Interrupted: %s", error)
            raise
