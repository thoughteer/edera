import pytest

from edera import Condition
from edera import Task
from edera.exceptions import LockAcquisitionError
from edera.exceptions import LockRetentionError
from edera.lockers import ProcessLocker
from edera.workflow import WorkflowBuilder
from edera.workflow.processors import TargetLocker


def test_target_locker_acquires_lock_first():

    class C(Condition):

        def check(self):
            return False

    class T(Task):

        target = C()

        def execute(self):
            raise RuntimeError

    workflow = WorkflowBuilder().build(T())
    locker = ProcessLocker()
    TargetLocker(locker).process(workflow)
    with locker.lock("C"):
        with pytest.raises(LockAcquisitionError):
            workflow[T()].item.execute()


def test_target_locker_prechecks_target():

    class C(Condition):

        def check(self):
            return True

    class T(Task):

        target = C()

        def execute(self):
            raise RuntimeError

    workflow = WorkflowBuilder().build(T())
    TargetLocker(ProcessLocker()).process(workflow)
    workflow[T()].item.execute()


def test_target_locker_executes_task_if_all_is_ok():

    class C(Condition):

        def check(self):
            return False

    class T(Task):

        target = C()

        def execute(self):
            raise RuntimeError

    workflow = WorkflowBuilder().build(T())
    TargetLocker(ProcessLocker()).process(workflow)
    with pytest.raises(RuntimeError):
        workflow[T()].item.execute()


def test_target_locker_interrupts_execution_on_lock_loss():

    class C(Condition):

        def check(self):
            return False

    class T(Task):

        target = C()

        def execute(self):
            raise RuntimeError

    class CrazyLocker(ProcessLocker):

        def lock(self, key, callback=None):
            callback()
            return super(CrazyLocker, self).lock(key)

    workflow = WorkflowBuilder().build(T())
    TargetLocker(CrazyLocker()).process(workflow)
    with pytest.raises(LockRetentionError):
        workflow[T()].item.execute()
