import logging
import os
import multiprocessing
import signal
import threading

from edera.exceptions import ExcusableError
from edera.flags import InterProcessFlag
from edera.worker import Worker


class ProcessWorker(Worker):
    """
    A worker that runs in a separate (forked) process.

    Attributes:
        process (Process) - the process created by the worker

    WARNING!
        Since this worker uses process forking, do not start it unless you are 100% sure
        there are no threads in your program which employ standard or non-standard modules that
        rely on module-level inter-thread locks (such as `logging` and `multiprocessing`).
        This may cause deadlocks in the forked process.
        For details, please, refer to http://bugs.python.org/issue6721.
        Moreover, avoid using $multiprocessing.Manager for inter-process communication.
        Stick to $multiprocessing.Queue and $multiprocessing.Lock primitives instead.
    """

    def __init__(self, name, action):
        self.__fail_flag = InterProcessFlag()
        self.__stop_flag = InterProcessFlag()
        self.process = multiprocessing.Process(target=self.__adapt_action(action), name=name)
        self.__started = False

    def __repr__(self):
        return "<%s: name %r - pid %r>" % (
            self.__class__.__name__,
            self.process.name,
            self.process.pid,
        )

    @property
    def alive(self):
        return self.process.is_alive()

    @property
    def failed(self):
        return self.__fail_flag.raised

    def join(self, timeout):
        assert self.__started
        self.process.join(timeout=timeout.total_seconds())

    def kill(self):
        assert self.__started
        try:
            os.kill(self.process.pid, signal.SIGKILL)
        except OSError:
            pass
        self.process.join()

    def start(self):
        assert not self.__started
        self.process.start()
        self.__started = True

    @property
    def stopped(self):
        return self.__stop_flag.raised

    def __adapt_action(self, action):

        def adapted_action():
            threading.current_thread().name = "-"
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
