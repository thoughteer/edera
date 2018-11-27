import pytest

from edera import Condition
from edera import Task
from edera.exceptions import ExcusableError
from edera.exceptions import ExcusableWorkflowExecutionError
from edera.exceptions import WorkflowExecutionError
from edera.requisites import shortcut
from edera.workflow import WorkflowBuilder
from edera.workflow.executors import BasicWorkflowExecutor
from edera.workflow.processors import TaskRanker


class AlreadyComplete(Condition):

    def check(self):
        return True


class A(Task):

    def execute(self):
        raise RuntimeError()

    @property
    def target(self):
        return AlreadyComplete()


class B(Task):

    @shortcut
    def requisite(self):
        return A()


class C(Task):

    def execute(self):
        raise ExcusableError()

    @shortcut
    def requisite(self):
        return {self: B(), D(): self}


class D(Task):

    def execute(self):
        raise RuntimeError()


class E(Task):

    def execute(self):
        pass

    @shortcut
    def requisite(self):
        return {self: B(), F(): self}


class F(Task):

    def execute(self):
        raise RuntimeError()


def test_basic_workflow_executor_finishes_if_all_is_ok():
    workflow = WorkflowBuilder().build(B())
    TaskRanker().process(workflow)
    BasicWorkflowExecutor().execute(workflow)


def test_basic_workflow_executor_handles_stopped_tasks_correctly():
    workflow = WorkflowBuilder().build(C())
    TaskRanker().process(workflow)
    with pytest.raises(ExcusableWorkflowExecutionError):
        BasicWorkflowExecutor().execute(workflow)


def test_basic_workflow_executor_handles_failed_tasks_correctly():
    workflow = WorkflowBuilder().build(E())
    TaskRanker().process(workflow)
    with pytest.raises(WorkflowExecutionError):
        BasicWorkflowExecutor().execute(workflow)
