from edera.requisites import shortcut
from edera.testing import AllTestSelector
from edera.testing import DefaultScenario
from edera.testing import RegexTestSelector
from edera.testing import TestableTask
from edera.workflow import WorkflowBuilder


def test_all_test_selector_selects_all_tests():

    class S1(DefaultScenario):
        pass

    class S2(DefaultScenario):
        pass

    class A(TestableTask):

        @property
        def tests(self):
            yield S1()
            yield S2()

    workflow = WorkflowBuilder().build(A())
    assert set(AllTestSelector().select(workflow, A())) == {S1(), S2()}


def test_regex_test_selector_works_correctly():

    class S1(DefaultScenario):
        pass

    class S2(DefaultScenario):
        pass

    class A(TestableTask):

        @shortcut
        def requisite(self):
            return B()

        @property
        def tests(self):
            yield S1()
            yield S2()

    class B(TestableTask):

        @property
        def tests(self):
            yield S1()
            yield S2()

    workflow = WorkflowBuilder().build(A())
    assert not set(RegexTestSelector([]).select(workflow, A()))
    assert not set(RegexTestSelector([("B", "")]).select(workflow, A()))
    assert not set(RegexTestSelector([("A", ".*3")]).select(workflow, A()))
    assert set(RegexTestSelector([("A.*", ".*1$")]).select(workflow, A())) == {S1()}
