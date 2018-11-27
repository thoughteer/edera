import logging

from edera.exceptions import LockRetentionError
from edera.flags import InterThreadFlag
from edera.routine import deferrable
from edera.routine import routine
from edera.task import TaskWrapper
from edera.workflow.processor import WorkflowProcessor
from edera.workflow.processors.target_prechecker import TargetPreCheckingTaskWrapper


class TargetLocker(WorkflowProcessor):
    """
    A workflow processor that makes tasks retain a lock during execution.

    Makes each task with a target to acquire a lock before actual execution.
    This ensures that only one instance of a task is active at a time.

    Pre-checks the target after successful lock acquisition in order to prevent double execution.

    Attributes:
        locker (Locker) - the locker used
    """

    def __init__(self, locker):
        """
        Args:
            locker (Locker) - a locker to use
        """
        self.locker = locker

    def process(self, workflow):
        for task in workflow:
            if task.target is None:
                continue
            task = TargetPreCheckingTaskWrapper(task)
            workflow.replace(TargetLockingTaskWrapper(task, self.locker))


class TargetLockingTaskWrapper(TaskWrapper):
    """
    A task wrapper that acquires a lock for its target before execution.

    Raises $LockRetentionError during execution if the lock gets lost.

    Attributes:
        locker (Optional[Locker]) - the locker used
    """

    def __init__(self, base, locker):
        """
        Args:
            base (Task) - a base task
            locker (Locker) - a locker to use
        """
        TaskWrapper.__init__(self, base)
        self.locker = locker

    @routine
    def execute(self):

        def check_loss_flag():
            if loss_flag.raised:
                raise LockRetentionError(self.target.name)

        loss_flag = InterThreadFlag()
        logging.getLogger(__name__).debug("Locking %r", self.target)
        with self.locker.lock(self.target.name, callback=loss_flag.up):
            try:
                deferred = deferrable(super(TargetLockingTaskWrapper, self).execute)
                yield deferred[check_loss_flag].defer()
            finally:
                logging.getLogger(__name__).debug("Unlocking %r", self.target)
