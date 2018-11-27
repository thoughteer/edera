from edera.linearizers import DFSLinearizer
from edera.workflow.processor import WorkflowProcessor


class TaskRanker(WorkflowProcessor):
    """
    A workflow processor that annotates each task with "rank" derived from a linearization
    of the workflow.

    Attributes:
        linearizer (Linearizer) - the linearizer used
    """

    def __init__(self, linearizer=DFSLinearizer()):
        """
        Args:
            linearizer (Linearizer) - a linearizer to use
        """
        self.linearizer = linearizer

    def process(self, workflow):
        for rank, task in enumerate(self.linearizer.linearize(workflow)):
            workflow[task]["rank"] = rank
