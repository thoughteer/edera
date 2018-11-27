import pytest

from edera import Condition
from edera import Task
from edera.exceptions import WorkflowNormalizationError
from edera.requisites import shortcut
from edera.workflow import WorkflowBuilder
from edera.workflow.processors import WorkflowNormalizer


class T(Task):

    class Target(Condition):

        def __init__(self, task):
            self.__name = task.name

        def check(self):
            return True

        @property
        def name(self):
            return self.__name

    @property
    def target(self):
        return self.Target(self)


def test_workflow_normalizer_ignores_normal_workflows():

    class A(T):
        pass

    class B(T):

        @shortcut
        def requisite(self):
            return A()

    workflow = WorkflowBuilder().build(B())
    assert WorkflowNormalizer.check(workflow)
    WorkflowNormalizer().process(workflow)


def test_workflow_normalizer_detects_simple_contradictions():

    class A(T):
        pass

    class N(Task):

        @shortcut
        def requisite(self):
            yield A()
            yield {B(): self}

    class B(T):

        target = ~A().target

    workflow = WorkflowBuilder().build(N())
    assert not WorkflowNormalizer.check(workflow)
    with pytest.raises(WorkflowNormalizationError):
        WorkflowNormalizer().process(workflow)


def test_workflow_normalizer_detects_complex_contradictions():

    class A(T):
        pass

    class B(T):

        target = ~A().target

    class C(T):

        @shortcut
        def requisite(self):
            return {self: B(), B(): A()}

    workflow = WorkflowBuilder().build(C())
    assert not WorkflowNormalizer.check(workflow)
    with pytest.raises(WorkflowNormalizationError):
        WorkflowNormalizer().process(workflow)


def test_workflow_normalizer_can_find_simple_pivot():

    class A(T):
        pass

    class B(T):

        @shortcut
        def requisite(self):
            yield A()
            yield {C(): self}

    class C(T):

        target = ~A().target

    workflow = WorkflowBuilder().build(B())
    assert not WorkflowNormalizer.check(workflow)
    WorkflowNormalizer().process(workflow)
    assert workflow[A()].item.target.expression == A().target.symbol | B().target.symbol
    assert workflow[B()].item.target == B().target
    assert workflow[C()].item.target.expression == C().target.symbol & B().target.symbol


def test_workflow_normalizer_can_find_complex_pivot():

    class X(Condition):

        def check(self):
            return True

    class B(T):
        pass

    class A(T):

        target = ~B().target | X()

    class W(T):

        @shortcut
        def requisite(self):
            return {B(): A()}

    workflow = WorkflowBuilder().build(W())
    assert not WorkflowNormalizer.check(workflow)
    WorkflowNormalizer().process(workflow)
    assert workflow[A()].item.target == A().target
    assert workflow[B()].item.target.expression == B().target.symbol & A().target.symbol


def test_workflow_normalizer_can_chain_corrections():

    class A(T):
        pass

    class B(T):

        @shortcut
        def requisite(self):
            return {self: A(), D(): self}

    class C(T):

        @shortcut
        def requisite(self):
            return {self: B(), E(): self}

    class D(T):

        target = ~A().target

    class E(T):

        target = ~B().target

    workflow = WorkflowBuilder().build(C())
    assert not WorkflowNormalizer.check(workflow)
    WorkflowNormalizer().process(workflow)
    assert workflow[A()].item.target.expression == (
        A().target.symbol | B().target.symbol | C().target.symbol
    )
    assert workflow[B()].item.target.expression == B().target.symbol | C().target.symbol
    assert workflow[C()].item.target == C().target
    assert workflow[D()].item.target.expression == (
        D().target.symbol & (B().target | C().target).symbol
    )
    assert workflow[E()].item.target.expression == E().target.symbol & C().target.symbol


def test_workflow_normalizer_can_handle_circular_dependencies():

    class A(T):
        pass

    class B(T):

        @shortcut
        def requisite(self):
            return {self: A(), C(): self}

    class C(T):

        target = A().target

    workflow = WorkflowBuilder().build(B())
    assert not WorkflowNormalizer.check(workflow)
    with pytest.raises(WorkflowNormalizationError):
        WorkflowNormalizer().process(workflow)
