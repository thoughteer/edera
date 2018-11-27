from edera import Task
from edera.requisites import shortcut
from edera.workflow import WorkflowBuilder
from edera.workflow.processors import TaskRanker


def test_task_ranker_assigns_correct_ranks():

    class T(Task):

        def __init__(self, index):
            self.index = index

        @property
        def name(self):
            return "T%d" % self.index

        @shortcut
        def requisite(self):
            return {T(i): self for i in range(self.index)}

    workflow = WorkflowBuilder().build(T(10))
    TaskRanker().process(workflow)
    assert all(workflow[T(i)]["rank"] == 10 - i for i in range(11))
