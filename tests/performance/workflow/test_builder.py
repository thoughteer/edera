import pytest

from edera import Task
from edera.requisites import shortcut
from edera.workflow import WorkflowBuilder


class T(Task):

    def __init__(self, index):
        self.index = index

    @property
    def name(self):
        return "T%d" % self.index

    @shortcut
    def requisite(self):
        return (T(i) for i in range(self.index))


@pytest.mark.parametrize("index", [1, 10, 100])
def test_builder_expands_requisites_fast_enough(benchmark, index):
    benchmark(WorkflowBuilder().build, T(index))
