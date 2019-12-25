from edera.workflow.processor import WorkflowProcessor
from edera.workflow.processors.target_postchecker import TargetPostChecker
from edera.workflow.processors.target_prechecker import TargetPreChecker


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
        TargetPostChecker().process(workflow)
        TargetPreChecker().process(workflow)
