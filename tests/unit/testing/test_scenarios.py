import pytest

from edera import Condition
from edera import Task
from edera.exceptions import TargetVerificationError
from edera.testing import DefaultScenario
from edera.testing import ScenarioWithProvidedStubs


def test_default_scenario_works_correctly():

    class A(Task):

        def execute(self):
            raise RuntimeError

    class B(Task):

        class T(Condition):

            def check(self):
                raise RuntimeError

        target = T()

    class Z(Task):

        class T(Condition):

            def check(self):
                return False

        target = T()

    scenario = DefaultScenario()
    assert scenario.stub(Z(), {A(), B()}) == {
        A(): DefaultScenario(),
        B(): DefaultScenario(),
    }
    with pytest.raises(RuntimeError):
        scenario.run(A())
    with pytest.raises(RuntimeError):
        scenario.run(B())
    with pytest.raises(TargetVerificationError):
        scenario.run(Z())


def test_scenario_with_provided_stubs_works_correctly():

    class A(Task):
        pass

    class B(Task):
        pass

    class Z(Task):
        pass

    class S(ScenarioWithProvidedStubs):

        def run(self, subject):
            pass

    stubs = {A(): DefaultScenario()}
    assert S(stubs=stubs).stub(Z(), {A(), B()}) == stubs
