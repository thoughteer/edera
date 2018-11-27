import logging

from edera.exceptions import TargetVerificationError
from edera.helpers import Phony
from edera.routine import deferrable
from edera.routine import routine
from edera.task import TaskWrapper
from edera.workflow.processor import WorkflowProcessor


class TargetPostChecker(WorkflowProcessor):
    """
    A workflow processor that makes tasks post-check targets.

    Patches each task to post-check its target after execution.
    These post-checks ensure that targets become $True after task execution.

    See also:
        $TargetChecker
        $TargetPreChecker
    """

    def process(self, workflow):
        for task in workflow:
            if task.execute is Phony:
                continue
            workflow.replace(TargetPostCheckingTaskWrapper(task))


class TargetPostCheckingTaskWrapper(TaskWrapper):
    """
    A task wrapper that post-checks the target.
    """

    @routine
    def execute(self):
        yield deferrable(super(TargetPostCheckingTaskWrapper, self).execute).defer()
        if self.target is not None:
            logging.getLogger(__name__).debug("Post-checking %r", self.target)
            completed = yield deferrable(self.target.check).defer()
            if not completed:
                raise TargetVerificationError(self)
