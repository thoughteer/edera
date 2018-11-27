import pytest

from edera import Condition
from edera import Task
from edera.requisites import shortcut
from edera.workflow import WorkflowBuilder
from edera.workflow.processors import WorkflowNormalizer


class FileExists(Condition):

    def __init__(self, index):
        self.index = index

    def check(self):
        return True

    @property
    def invariants(self):
        if self.index == 0:
            return
        yield self >> FileExists(0)

    @property
    def name(self):
        return "FileExists%d" % self.index


class Prepare(Task):

    target = FileExists(0)


class Create(Task):

    def __init__(self, index):
        self.index = index

    @property
    def name(self):
        return "Create%d" % self.index

    @shortcut
    def requisite(self):
        yield Prepare()
        if self.index == 1:
            return
        yield Create(self.index - 1)
        yield {Remove(self.index - 1): self}

    @property
    def target(self):
        return FileExists(self.index)


class Remove(Task):

    def __init__(self, index):
        self.index = index

    @property
    def name(self):
        return "Remove%d" % self.index

    @property
    def target(self):
        return ~FileExists(self.index)


@pytest.mark.parametrize("index", [1, 10, 25, 50])
def test_workflow_normalizer_works_fast_enough(benchmark, index):
    workflow = WorkflowBuilder().build(Create(index))
    benchmark(lambda: WorkflowNormalizer().process(workflow.clone()))
