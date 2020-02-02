from edera import Task
from edera.requisites import shortcut
from edera.requisites import Annotate
from edera.workflow import WorkflowBuilder
from edera.workflow.processors import TagFilter


def test_tag_filter_works_correctly():

    class A(Task):

        @shortcut
        def requisite(self):
            yield {C(): self}

    class B(Task):

        @shortcut
        def requisite(self):
            yield A()
            yield {D(): self}

    class C(Task):
        pass

    class D(Task):
        pass

    class E(Task):

        @shortcut
        def requisite(self):
            yield Annotate("tag", "X")
            yield B()

    workflow = WorkflowBuilder().build(E())
    TagFilter("X").process(workflow)
    assert set(workflow) == {A(), B(), E()}
    assert workflow[B()].parents == {A()}
    assert workflow[E()].parents == {B()}
    TagFilter(None).process(workflow)
    assert set(workflow) == {A(), B()}
    assert workflow[B()].parents == {A()}
    TagFilter("Z").process(workflow)
    assert len(workflow) == 0
