import pytest

from edera import Task
from edera.exceptions import WorkflowTestificationError
from edera.requisites import shortcut
from edera.storages import InMemoryStorage
from edera.testing import DefaultScenario
from edera.testing import TestableTask
from edera.workflow import WorkflowBuilder
from edera.workflow.processors import WorkflowTestifier


def test_workflow_testifier_notifies_about_overstubbing():

    class A(Task):
        pass

    class B(TestableTask):

        @shortcut
        def requisite(self):
            return A()

        @property
        def tests(self):
            yield InvalidScenario()

    class InvalidScenario(DefaultScenario):

        def stub(self, subject, dependencies):
            return {B(): DefaultScenario()}  # not in the $dependencies

    workflow = WorkflowBuilder().build(B())
    cache = InMemoryStorage()
    with pytest.raises(WorkflowTestificationError):
        WorkflowTestifier(cache).process(workflow)


def test_workflow_testifier_notifies_about_scenario_conflicts():

    class A(Task):
        pass

    class B(Task):

        @shortcut
        def requisite(self):
            return A()

    class C(TestableTask):

        @shortcut
        def requisite(self):
            return [A(), B()]

        @property
        def tests(self):
            yield InvalidScenarioForC()

    class InvalidScenarioForC(DefaultScenario):

        def stub(self, subject, dependencies):
            return {
                A(): DefaultScenario(),  # 1
                B(): SpecialScenarioForB(),
            }

    class SpecialScenarioForB(DefaultScenario):

        def stub(self, subject, dependencies):
            return {A(): SpecialScenarioForA()}  # 2

    class SpecialScenarioForA(DefaultScenario):
        pass

    workflow = WorkflowBuilder().build(C())
    cache = InMemoryStorage()
    with pytest.raises(WorkflowTestificationError):
        WorkflowTestifier(cache).process(workflow)


def test_workflow_testifier_colorizes_tasks_accordingly():

    class A(Task):
        pass

    class B(Task):
        pass

    class C(TestableTask):

        @shortcut
        def requisite(self):
            return [A(), B()]

        @property
        def tests(self):
            yield ScenarioForC()

    class D(TestableTask):

        @shortcut
        def requisite(self):
            return [A(), B()]

        @property
        def tests(self):
            yield ScenarioForD()

    class E(Task):

        @shortcut
        def requisite(self):
            return [C(), D()]

    class ScenarioForC(DefaultScenario):

        def stub(self, subject, dependencies):
            return {A(): DefaultScenario(), B(): DefaultScenario()}

    class ScenarioForD(DefaultScenario):

        def stub(self, subject, dependencies):
            return {A(): DefaultScenario(), B(): SpecialScenarioForB()}

    class SpecialScenarioForB(DefaultScenario):
        pass

    workflow = WorkflowBuilder().build(E())
    cache = InMemoryStorage()
    WorkflowTestifier(cache).process(workflow)
    assert len(workflow) == 6


def test_workflow_testifier_works_correctly():

    class A(Task):
        pass

    class B(TestableTask):

        @property
        def tests(self):
            yield DefaultScenario()

    class C(Task):

        @shortcut
        def requisite(self):
            return A()

    class D(TestableTask):

        @shortcut
        def requisite(self):
            return [A(), B(), C()]

        @property
        def tests(self):
            yield FirstScenarioForD()
            yield SecondScenarioForD()

    class E(TestableTask):

        @shortcut
        def requisite(self):
            return [C(), D()]

        @property
        def tests(self):
            yield ScenarioForE()

    class FirstScenarioForD(DefaultScenario):

        def stub(self, subject, dependencies):
            return {A(): DefaultScenario(), B(): DefaultScenario()}

    class SecondScenarioForD(DefaultScenario):

        def stub(self, subject, dependencies):
            return {A(): SpecialScenarioForA()}

    class SpecialScenarioForA(DefaultScenario):
        pass

    class ScenarioForE(DefaultScenario):

        def stub(self, subject, dependencies):
            return {C(): DefaultScenario()}

    workflow = WorkflowBuilder().build(E())
    cache = InMemoryStorage()
    WorkflowTestifier(cache).process(workflow)
    assert len(workflow) == 8
    assert sum(len(workflow[task].parents) for task in workflow) == 6
    assert len(set(workflow[task]["color"] for task in workflow)) == 2
