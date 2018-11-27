import pytest

from edera import Parameter
from edera import Parameterizable
from edera.qualifiers import Integer
from edera.requisites import shortcut
from edera.storages import InMemoryStorage
from edera.testing import DefaultScenario
from edera.testing import TestableTask
from edera.workflow import WorkflowBuilder
from edera.workflow.processors import WorkflowTestifier


class T(Parameterizable, TestableTask):

    i = Parameter(Integer)

    @shortcut
    def requisite(self):
        if self.i == 0:
            return
        return T(i=(self.i - 1))

    @property
    def tests(self):
        yield S()


class S(DefaultScenario):

    def stub(self, subject, dependencies):
        return {dependency: F() for dependency in dependencies}


class F(DefaultScenario):

    def stub(self, subject, dependencies):
        return {}


@pytest.mark.parametrize("index", [1, 10, 100, 1000, 5000])
def test_workflow_testifier_works_fast_enough(benchmark, index):
    workflow = WorkflowBuilder().build(T(i=index))
    cache = InMemoryStorage()
    benchmark(lambda: WorkflowTestifier(cache).process(workflow.clone()))
