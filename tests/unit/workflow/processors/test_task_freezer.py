from edera import Task
from edera.workflow import WorkflowBuilder
from edera.workflow.processors import TaskFreezer


def test_task_freezer_computes_properties_only_once():

    class T(Task):

        @property
        def requisite(self):
            counter[0] += 1

        @property
        def target(self):
            counter[0] += 1

    counter = [0]
    workflow = WorkflowBuilder().build(T())
    assert counter[0] == 1
    TaskFreezer().process(workflow)
    [task.requisite for task in workflow]
    [task.target for task in workflow]
    assert counter[0] == 3
