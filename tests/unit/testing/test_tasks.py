import pytest

from edera import Condition
from edera import Task
from edera.requisites import shortcut
from edera.storages import InMemoryStorage
from edera.testing import DefaultScenario
from edera.testing import Stub
from edera.testing import Test
from edera.testing import TestableTask
from edera.workflow import WorkflowBuilder


def test_testable_task_annotates_itself():

    class S(DefaultScenario):
        pass

    class A(TestableTask):
        pass

    class B(TestableTask):

        def execute(self):
            pass

    class C(TestableTask):

        @shortcut
        def requisite(self):
            return [A(), B()]

        @property
        def tests(self):
            yield S()

    workflow = WorkflowBuilder().build(C())
    assert workflow[A()]["tests"] == set()
    assert workflow[B()]["tests"] == {DefaultScenario()}
    assert workflow[C()]["tests"] == {S()}


def test_testing_task_has_correct_target():

    class A(Task):
        pass

    class T(Test):

        registry = InMemoryStorage()

    test = T(scenario=DefaultScenario(), subject=A())
    assert not test.target.check()
    test.execute()
    assert test.target.check()


def test_testing_task_runs_scenario():

    class A(Task):

        def execute(self):
            raise RuntimeError

    class T(Test):

        registry = InMemoryStorage()

    test = T(scenario=DefaultScenario(), subject=A())
    assert not set(test.target.invariants)
    assert not test.target.check()
    with pytest.raises(RuntimeError):
        test.execute()
    assert not test.target.check()


def test_testing_task_postchecks_target():

    class E(Condition):

        def check(self):
            raise RuntimeError

    class A(Task):

        target = E()

    class T(Test):

        registry = InMemoryStorage()

    test = T(scenario=DefaultScenario(), subject=A())
    assert (test.target >> E()) in set(test.target.invariants)
    assert not test.target.check()
    with pytest.raises(RuntimeError):
        test.execute()
    assert not test.target.check()


def test_stubbing_task_runs_scenario():

    class F(Condition):

        def check(self):
            return False

    class A(Task):

        target = F()

        def execute(self):
            raise RuntimeError

    stub = Stub(scenario=DefaultScenario(), subject=A())
    assert stub.target == F()
    with pytest.raises(RuntimeError):
        stub.execute()
