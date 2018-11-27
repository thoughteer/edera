import pytest

from edera import Condition
from edera import Task
from edera.exceptions import TargetVerificationError
from edera.workflow import WorkflowBuilder
from edera.workflow.processors import TargetChecker


def test_target_checker_skips_task_execution_if_possible():

    class C(Condition):

        def check(self):
            return True

    class T(Task):

        target = C()

        def execute(self):
            raise RuntimeError

    workflow = WorkflowBuilder().build(T())
    TargetChecker().process(workflow)
    workflow[T()].item.execute()


def test_target_checker_verifies_target_after_task_execution():

    class C(Condition):

        def check(self):
            return False

    class T(Task):

        target = C()

        def execute(self):
            pass

    workflow = WorkflowBuilder().build(T())
    TargetChecker().process(workflow)
    with pytest.raises(TargetVerificationError):
        workflow[T()].item.execute()
