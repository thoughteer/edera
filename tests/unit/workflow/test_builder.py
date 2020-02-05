from edera import Task
from edera.requisites import Annotate
from edera.requisites import ExtendAnnotation
from edera.requisites import shortcut
from edera.workflow import WorkflowBuilder


class A(Task):

    @shortcut
    def requisite(self):
        return B()


class B(Task):

    @shortcut
    def requisite(self):
        yield C()
        yield D()


class C(Task):

    @shortcut
    def requisite(self):
        return {
            Z(): [B(), D()],
            E(): [A(), Z()],
        }


class D(Task):

    @shortcut
    def requisite(self):
        yield Annotate(key="simple", value="value")
        yield ExtendAnnotation(key="complex", values={"v1", "v2"})


class E(Task):
    pass


class Z(Task):
    pass


def test_builder_builds_workflow_correctly():
    workflow = WorkflowBuilder().build(A())
    assert workflow[A()].item == A()
    assert workflow[A()].children == {E()}
    assert workflow[A()].parents == {B()}
    assert workflow[B()].item == B()
    assert workflow[B()].children == {A(), Z()}
    assert workflow[B()].parents == {C(), D()}
    assert workflow[C()].item == C()
    assert workflow[C()].children == {B()}
    assert not workflow[C()].parents
    assert workflow[D()].item == D()
    assert workflow[D()].children == {B(), Z()}
    assert not workflow[D()].parents
    assert workflow[D()].annotation == {"simple": "value", "complex": {"v1", "v2"}}
    assert workflow[E()].item == E()
    assert not workflow[E()].children
    assert workflow[E()].parents == {A(), Z()}
    assert workflow[Z()].item == Z()
    assert workflow[Z()].children == {E()}
    assert workflow[Z()].parents == {B(), D()}
