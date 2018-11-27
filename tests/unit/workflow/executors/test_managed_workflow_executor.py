import contextlib

import pytest

from edera import Task
from edera.exceptions import WorkflowExecutionError
from edera.workflow import WorkflowBuilder
from edera.workflow.executors import BasicWorkflowExecutor
from edera.workflow.executors import ManagedWorkflowExecutor
from edera.workflow.processors import TaskRanker


class T(Task):

    def execute(self):
        raise RuntimeError()


def test_managed_workflow_executor_employs_manager():

    @contextlib.contextmanager
    def incrementer():
        counter[0] += 1
        try:
            yield
        finally:
            counter[0] += 1

    counter = [0]
    workflow = WorkflowBuilder().build(T())
    TaskRanker().process(workflow)
    with pytest.raises(WorkflowExecutionError):
        ManagedWorkflowExecutor(BasicWorkflowExecutor(), incrementer()).execute(workflow)
    assert counter[0] == 2
