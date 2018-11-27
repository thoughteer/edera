import logging

from edera.helpers import Phony
from edera.routine import deferrable
from edera.routine import routine
from edera.task import TaskWrapper
from edera.workflow.processor import WorkflowProcessor


class TargetPreChecker(WorkflowProcessor):
    """
    A workflow processor that makes tasks pre-check targets.

    Patches each task to pre-check its target before actual execution.
    These pre-checks prevent running already completed tasks.

    See also:
        $TargetChecker
        $TargetPostChecker
    """

    def process(self, workflow):
        for task in workflow:
            if task.execute is Phony:
                continue
            workflow.replace(TargetPreCheckingTaskWrapper(task))


class TargetPreCheckingTaskWrapper(TaskWrapper):
    """
    A task wrapper that pre-checks the target.
    """

    @routine
    def execute(self):
        if self.target is not None:
            logging.getLogger(__name__).debug("Pre-checking %r", self.target)
            completed = yield deferrable(self.target.check).defer()
            if completed:
                logging.getLogger(__name__).debug("Task %r already completed (skipping)", self)
                return
        yield deferrable(super(TargetPreCheckingTaskWrapper, self).execute).defer()
