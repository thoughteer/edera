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


class StillIncomplete(Condition):

    def check(self):
        return False


@pytest.mark.parametrize("n", [1, 2, 3, 5, 10, 19])
def test_workflow_trimmer_trims_linear_workflow_well(n):

    class T(Parameterizable, Task):

        i = Parameter(Integer)
        s = Parameter(Integer)

        @shortcut
        def requisite(self):
            if self.i == 0:
                return
            return T(i=(self.i - 1), s=self.s)

        @property
        def target(self):
            return AlreadyComplete() if self.i < self.s else StillIncomplete()

    for s in range(n):
        workflow = WorkflowBuilder().build(T(i=(n - 1), s=s))
        WorkflowTrimmer().process(workflow)
        assert all(T(i=i, s=s) in workflow for i in range(s, n))
        assert len(workflow) <= n - s + 3


@pytest.mark.parametrize("n", [1, 2, 3, 5, 10])
def test_workflow_trimmer_trims_nn_workflow_well(n):

    class T(Parameterizable, Task):

        i = Parameter(Integer)
        j = Parameter(Integer)
        s = Parameter(Integer)

        @shortcut
        def requisite(self):
            if self.i == 0:
                return
            return (T(i=(self.i - 1), j=j, s=self.s) for j in range(n))

        @property
        def target(self):
            return AlreadyComplete() if self.i < self.s else StillIncomplete()

    class W(Parameterizable, Task):

        s = Parameter(Integer)

        @shortcut
        def requisite(self):
            return (T(i=(n - 1), j=j, s=self.s) for j in range(n))

    for s in range(n):
        workflow = WorkflowBuilder().build(W(s=s))
        WorkflowTrimmer().process(workflow)
        assert all(T(i=i, j=j, s=s) in workflow for i in range(s, n) for j in range(n))
        assert len(workflow) <= (n - s + 1) * n + 1
