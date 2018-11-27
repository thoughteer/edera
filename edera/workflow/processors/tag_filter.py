from edera.linearizers import DFSLinearizer
from edera.workflow.processor import WorkflowProcessor


class TagFilter(WorkflowProcessor):
    """
    A workflow processor that filters out tasks that do not affect tasks with the given tag.

    A task gets removed from the workflow iff its tag (if any) differs from the given one and
    it has no followers with the given tag.

    Attributes:
        tag (String) - the tag value to filter by
    """

    def __init__(self, tag):
        """
        Args:
            tag (String) - a tag value to filter by
        """
        self.tag = tag

    def process(self, workflow):
        foreigners = set()
        for task in reversed(DFSLinearizer().linearize(workflow)):
            tag = workflow[task].annotation.get("tag")
            if self.tag != tag and workflow[task].children <= foreigners:
                foreigners.add(task)
        workflow.remove(*foreigners)
