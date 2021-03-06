import pytest

from edera import Condition
from edera import Task
from edera.exceptions import TargetVerificationError
from edera.requisites import shortcut
from edera.workflow import WorkflowBuilder
from edera.workflow.processors import TargetPostChecker


def test_target_postchecker_always_executes_task():

    class C(Condition):

        def check(self):
            return True

    class T(Task):

        target = C()

        def execute(self):
            pass

    class X(Task):

        @shortcut
        def requisite(self):
            return T()

    workflow = WorkflowBuilder().build(X())
    TargetPostChecker().process(workflow)
    assert workflow[X()].item.phony
    workflow[T()].item.execute()


def test_target_postchecker_verifies_target_after_task_execution():

    class C(Condition):

        def check(self):
            return False

    class T(Task):

        target = C()

        def execute(self):
            pass

    workflow = WorkflowBuilder().build(T())
    TargetPostChecker().process(workflow)
    with pytest.raises(TargetVerificationError):
        workflow[T()].item.execute()
