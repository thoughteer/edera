import pytest

from edera import Condition
from edera import Task
from edera.requisites import shortcut
from edera.workflow import WorkflowBuilder
from edera.workflow.processors import TargetPreChecker


def test_target_prechecker_executes_task_if_necessary():

    class C(Condition):

        def check(self):
            return False

    class T(Task):

        target = C()

        def execute(self):
            raise RuntimeError

    class X(Task):

        @shortcut
        def requisite(self):
            return T()

    workflow = WorkflowBuilder().build(X())
    TargetPreChecker().process(workflow)
    assert workflow[X()].item.phony
    with pytest.raises(RuntimeError):
        workflow[T()].item.execute()


def test_target_prechecker_skips_task_execution_if_possible():

    class C(Condition):

        def check(self):
            return True

    class T(Task):

        target = C()

        def execute(self):
            raise RuntimeError

    workflow = WorkflowBuilder().build(T())
    TargetPreChecker().process(workflow)
    workflow[T()].item.execute()
