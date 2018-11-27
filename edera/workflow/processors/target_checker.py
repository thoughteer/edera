from edera.helpers import Phony
from edera.workflow.processor import WorkflowProcessor
from edera.workflow.processors.target_postchecker import TargetPostCheckingTaskWrapper
from edera.workflow.processors.target_prechecker import TargetPreCheckingTaskWrapper


class TargetChecker(WorkflowProcessor):
    """
    A workflow processor that makes tasks check targets.

    Patches each task to pre-check and post-check its target before and after execution,
    respectively.

    See also:
        $TargetPostChecker
        $TargetPreChecker
    """

    def process(self, workflow):
        for task in workflow:
            if task.execute is Phony:
                continue
            workflow.replace(TargetPreCheckingTaskWrapper(TargetPostCheckingTaskWrapper(task)))
