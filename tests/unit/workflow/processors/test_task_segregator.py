from edera import Condition
from edera import Task
from edera.helpers import SimpleBox
from edera.requisites import shortcut
from edera.requisites import Annotate
from edera.workflow import WorkflowBuilder
from edera.workflow.executors import BasicWorkflowExecutor
from edera.workflow.processors import TaskRanker
from edera.workflow.processors import TaskSegregator


def test_task_segregator_fills_box_correctly():

    COLOR = SimpleBox()
    DONE = set()

    class F(Condition):

        def check(self):
            assert COLOR.get() == "1"
            DONE.add(self)
            return False

    class A(Task):

        target = F()

        @property
        def requisite(self):
            return Annotate("color", "1")

        def execute(self):
            assert COLOR.get() == "1"
            DONE.add(self)

    class B(Task):

        @shortcut
        def requisite(self):
            yield Annotate("color", "1")
            yield A()

        def execute(self):
            assert COLOR.get() == "1"
            assert A() in DONE
            DONE.add(self)

    class C(Task):

        @property
        def requisite(self):
            return Annotate("color", "2")

        def execute(self):
            assert COLOR.get() == "2"
            DONE.add(self)

    class X(Task):

        @shortcut
        def requisite(self):
            return [B(), C()]

        def execute(self):
            assert COLOR.get() is None
            DONE.add(self)

    class Y(Task):

        @shortcut
        def requisite(self):
            return X()

    workflow = WorkflowBuilder().build(Y())
    TaskRanker().process(workflow)
    TaskSegregator(COLOR).process(workflow)
    assert workflow[Y()].item.phony
    BasicWorkflowExecutor().execute(workflow)
    assert COLOR.get() is None
    assert DONE == {F(), A(), B(), C(), X()}
