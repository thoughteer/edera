import pytest

from edera import Condition
from edera import Parameter
from edera import Parameterizable
from edera import Task
from edera.qualifiers import Integer
from edera.requisites import shortcut
from edera.workflow import WorkflowBuilder
from edera.workflow.processors import WorkflowTrimmer


class AlreadyComplete(Condition):

    def check(self):
        return True


@pytest.mark.parametrize("n", [1, 10, 100, 1000])
def test_workflow_trimmer_trims_linear_workflow_very_fast(benchmark, n):

    class T(Parameterizable, Task):

        i = Parameter(Integer)

        @shortcut
        def requisite(self):
            if self.i == 0:
                return
            return T(i=(self.i - 1))

        @property
        def target(self):
            return AlreadyComplete()

    benchmark(lambda: WorkflowTrimmer().process(WorkflowBuilder().build(T(i=(n - 1)))))


@pytest.mark.parametrize("n", [1, 5, 10, 25])
def test_workflow_trimmer_trims_nn_workflow_fast_enough(benchmark, n):

    class T(Parameterizable, Task):

        i = Parameter(Integer)
        j = Parameter(Integer)

        @shortcut
        def requisite(self):
            if self.i == 0:
                return
            return (T(i=(self.i - 1), j=j) for j in range(n))

        @property
        def target(self):
            return AlreadyComplete()

    class W(Task):

        @shortcut
        def requisite(self):
            return (T(i=(n - 1), j=j) for j in range(n))

    benchmark(lambda: WorkflowTrimmer().process(WorkflowBuilder().build(W())))
