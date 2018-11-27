import datetime
import logging

import six

from edera.exceptions import ExcusableMasterSlaveInvocationError
from edera.exceptions import MasterSlaveInvocationError
from edera.helpers import CurrentException
from edera.helpers import Factory
from edera.invoker import Invoker
from edera.routine import deferrable
from edera.routine import routine


class MasterSlaveInvoker(Factory[Invoker]):
    """
    A generic master-slave invoker.

    Runs several functions in parallel in separate workers and waits for them to finish.
    The master interrupts workers by raising a flag (if needed).
    The worker class and the flag class should be passed as a cargo.

    This invoker is interruptible.

    Attributes:
        actions (Mapping[String, Callable[[], Any]]) - the action functions
        interruption_timeout (TimeDelta) - time to wait for the actions to finish
                after being interrupted

    Constants:
        _SINGLE_JOIN_ATTEMPT_TIMEOUT (TimeDelta) - time to wait for each join attempt

    See also:
        $Factory
        $Worker
    """

    _SINGLE_JOIN_ATTEMPT_TIMEOUT = datetime.timedelta(milliseconds=250)

    def __init__(self, actions, interruption_timeout=datetime.timedelta(minutes=1)):
        """
        Args:
            actions (Mapping[String, Callable[[], Any]]) - a named set of functions to call
            interruption_timeout (TimeDelta) - time to wait for the functions to finish
                    after being interrupted
                Default is 1 minute.

        After $interruption_timeout since the moment $invoke was interrupted the invoker
        will kill all its slave workers.
        It's a violent procedure, so make sure you interrupt every non-$Routine action on your own
        in order to stop gracefully.

        See also:
            $Routine
        """
        self.actions = actions
        self.interruption_timeout = interruption_timeout

    @routine
    def invoke(self):
        """
        Raises:
            ExcusableMasterSlaveInvocationError if some of the slaves stopped (and no one failed)
            MasterSlaveInvocationError if some of the slaves failed

        See also:
            $ExcusableMasterSlaveInvocationError
            $MasterSlaveInvocationError
        """

        def check_interruption_flag():
            if interruption_flag.raised:
                raise SystemExit("interrupted by the master")

        interruption_flag = self.cargo[1]()
        slaves = [
            self.cargo[0](name, deferrable(action)[check_interruption_flag])
            for name, action in six.iteritems(self.actions)
        ]
        logging.getLogger(__name__).debug("Starting slaves")
        for slave in slaves:
            slave.start()
        running = True
        killing = False
        interruption_time = None
        interrupting_exception = None
        while running and not killing:
            if interruption_time is None:
                try:
                    yield
                except BaseException:
                    logging.getLogger(__name__).debug("Interrupted")
                    interruption_flag.up()
                    interruption_time = datetime.datetime.utcnow()
                    interrupting_exception = CurrentException()
            for slave in slaves:
                slave.join(self._SINGLE_JOIN_ATTEMPT_TIMEOUT / len(slaves))
            running = any(slave.alive for slave in slaves)
            if interruption_time is not None:
                killing = datetime.datetime.utcnow() - interruption_time > self.interruption_timeout
        if killing:
            logging.getLogger(__name__).debug("Killing slaves")
            for slave in slaves:
                slave.kill()
        if interrupting_exception is not None:
            interrupting_exception.reraise()
        failed_slaves = [slave for slave in slaves if slave.failed]
        if failed_slaves:
            raise MasterSlaveInvocationError(failed_slaves)
        stopped_slaves = [slave for slave in slaves if slave.stopped]
        if stopped_slaves:
            raise ExcusableMasterSlaveInvocationError(stopped_slaves)

    @classmethod
    def replicate(
            cls, action, count, prefix="W-", interruption_timeout=datetime.timedelta(minutes=1)):
        """
        Replicate the same action multiple times and run in parallel.

        Args:
            action (Callable[[], Any]) - an action function to replicate
            count (Integer) - the number of workers
            prefix (String) - a prefix string used to form the name of the workers
                Default is "W-".
            interruption_timeout (TimeDelta) - time to wait for the functions to finish
                    after being interrupted
                Default is 1 minute.

        Returns:
            MasterSlaveInvoker
        """
        actions = {("%s%d" % (prefix, index + 1)): action for index in range(count)}
        return cls(actions, interruption_timeout=interruption_timeout)
