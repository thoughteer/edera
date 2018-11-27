import datetime
import signal
import threading
import time

import six


class Sasha(object):
    """
    A safe asynchronous signal handling agent.

    Suppose you'd like to write some useful information to the log every time your Python
    application receives the SIGUSR1 signal.
    Easy, huh?

        >>> import logging
        >>> import signal
        >>> def handle(*args, **kwargs):
        >>>     logging.getLogger(__name__).info("My useful information")
        >>> signal.signal(signal.SIGUSR1, handle)
        >>> # do stuff

    But there are three things you need to know:
     1. Signal handling in Python is a bit weird, so the handler will be called at some
        arbitrary distant moment in the future somewhere in the middle of the byte-code.
     2. Internally, many standard modules like $logging and $multiprocessing actively use global
        reentrant locks.
        For instance, $logging acquires its global reentrant lock on each $getLogger call.
     3. Python doesn't support critical (atomic) sections (the ones that can't be interrupted
        by the interpreter).
        So, $RLock's implementation, which combines a $Lock with a reference to the owner thread
        to provide reentrancy, becomes non-reentrant as soon as you interrupt it
        (with a signal) right between acquiring the $Lock and storing the reference.
    Putting it all together, we conclude that the aforementioned solution will just hang
    occasionally, and it would be really hard to reproduce.

    $Sasha, on the other hand, allows you to set any signal handlers safely.
    It works by registering incoming signals in a temporary dictionary (this operation is
    as simple as it could get and requires no locking), and watching for the dictionary changes
    in separate daemon threads (one per handled signal).
    Here is a better solution to the original problem using $Sasha:

        >>> from edera.sasha import Sasha
        >>> import signal
        >>> def handle():
        >>>     logging.getLogger(__name__).info("My useful information")
        >>> with Sasha({signal.SIGUSR1: handle}):
        >>>     # do stuff

    Please, keep in mind that
      - $Sasha is a non-reentrant context manager:

        >>> sasha = Sasha({signal.SIGUSR1: handle})
        >>> with sasha:
        >>>     with sasha:  # AssertionError
        >>>         pass

      - $Sasha may "collapse" signals of the same type if they occur quickly in a row:

        >>> def handle():
        >>>     print("SIGINT")
        >>> with Sasha({signal.SIGINT: handle}):
        >>>     os.kill(os.getpid(), signal.SIGINT)
        >>>     os.kill(os.getpid(), signal.SIGINT)  # may not take effect
        >>>     time.sleep(10.0)
        >>> # most likely, "SIGINT" will be printed only once

      - $Sasha expects smoothly working handlers - try not to hang or raise an exception

    Attributes:
        handlers (Mapping[Signal, Callable[[], Any]]) - the signal handlers
        interval (TimeDelta) - the interval between asynchronous checks
    """

    INACTIVE = 0
    ACTIVATING = 1
    ACTIVE = 2

    def __enter__(self):
        assert self.__state == self.INACTIVE
        self.__state = self.ACTIVATING
        self.__activate()
        self.__state = self.ACTIVE

    def __exit__(self, *args):
        self.__state = self.INACTIVE
        self.__stop_asynchronous_handlers()
        self.__restore_original_signal_handlers()

    def __init__(self, handlers, interval=datetime.timedelta(milliseconds=100)):
        """
        Args:
            handlers (Mapping[Signal, Callable[[], Any]]) - signal handlers
            interval (TimeDelta) - an interval between asynchronous checks
                Default is 100 milliseconds.
        """
        self.handlers = handlers
        self.interval = interval
        self.__state = self.INACTIVE
        self.__original_handlers = {}
        self.__threads = []

    def __activate(self):
        flags = {sid: False for sid in self.handlers}
        for sid in flags:
            self.__set_signal_handler(flags, sid)
            self.__start_asynchronous_handler(flags, sid)

    def __restore_original_signal_handlers(self):
        for sid, handler in six.iteritems(self.__original_handlers):
            signal.signal(sid, handler)

    def __set_signal_handler(self, flags, sid):

        def handle(*args, **kwargs):
            if self.__state == self.ACTIVE:
                flags[sid] = True

        self.__original_handlers[sid] = signal.signal(sid, handle)

    def __start_asynchronous_handler(self, flags, sid):

        def handle():
            while self.__state != self.INACTIVE:
                if self.__state == self.ACTIVE and flags[sid]:
                    self.handlers[sid]()
                    flags[sid] = False
                time.sleep(self.interval.total_seconds())

        thread = threading.Thread(target=handle)
        thread.daemon = True
        thread.start()
        self.__threads.append(thread)

    def __stop_asynchronous_handlers(self):
        for thread in self.__threads:
            thread.join()
        self.__threads = []
