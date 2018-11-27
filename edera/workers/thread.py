import logging
import threading

from edera.exceptions import ExcusableError
from edera.flags import InterThreadFlag
from edera.worker import Worker


class ThreadWorker(Worker):
    """
    A worker that runs in a separate thread.

    Attributes:
        thread (Thread) - the thread created by the worker
    """

    def __init__(self, name, action):
        self.__fail_flag = InterThreadFlag()
        self.__stop_flag = InterThreadFlag()
        self.__started = False
        self.__killed = False
        self.thread = threading.Thread(target=self.__adapt_action(action), name=name)
        self.thread.daemon = True

    def __repr__(self):
        return "<%s: name %r>" % (self.__class__.__name__, self.thread.name)

    @property
    def alive(self):
        return self.thread.is_alive() and not self.__killed

    @property
    def failed(self):
        return self.__fail_flag.raised

    def join(self, timeout):
        assert self.__started
        self.thread.join(timeout=timeout.total_seconds())

    def kill(self):
        assert self.__started
        self.__killed = True

    def start(self):
        assert not self.__started
        self.thread.start()
        self.__started = True

    @property
    def stopped(self):
        return self.__stop_flag.raised

    def __adapt_action(self, action):

        def adapted_action():
            try:
                action()
            except SystemExit as error:
                logging.getLogger(__name__).debug("Worker %r was terminated: %s", self, error)
            except ExcusableError as error:
                logging.getLogger(__name__).debug("Worker %r stopped: %s", self, error)
                self.__stop_flag.up()
            except BaseException:
                logging.getLogger(__name__).debug("Worker %r failed:", self, exc_info=True)
                self.__fail_flag.up()

        return adapted_action
