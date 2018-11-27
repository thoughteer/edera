import abc

from edera.condition import Condition
from edera.helpers import Phony
from edera.parameterizable import Parameter
from edera.parameterizable import Parameterizable
from edera.qualifiers import Instance
from edera.requisites import Annotate
from edera.routine import deferrable
from edera.routine import routine
from edera.task import Task
from edera.testing.scenarios import DefaultScenario
from edera.testing.scenarios import Scenario


class TestableTask(Task):
    """
    A task class that automatically annotates itself with "tests".

    The "tests" annotation is taken from the "tests" attribute and defines the list of available
    testing scenarios for the task.
    $DefaultScenario will be used if you don't provide a custom value.

    Attributes:
        tests (Iterable[Scenario]) - the list of available testing scenarios

    See also:
        $Stub
        $Test
    """

    @property
    def requisite(self):
        return Annotate("tests", self.tests)

    @property
    def tests(self):
        if self.execute is not Phony:
            yield DefaultScenario()


class Test(Parameterizable, Task):
    """
    An abstract class for testing tasks used to check the correctness of a subject task.

    Runs the $scenario for the $subject and registers itself in the $cache if no errors
    occurred (meaning, the test has passed).

    Attributes:
        cache (Storage) - the storage used to store passed tests
    """

    scenario = Parameter(Instance[Scenario])
    subject = Parameter(Instance[Task])

    @abc.abstractproperty
    def cache(self):
        pass

    @routine
    def execute(self):
        yield deferrable(self.scenario.run).defer(self.subject)
        if self.cache.get(self.name, limit=1):
            return
        self.cache.put(self.name, "!")

    @property
    def target(self):
        return TestPassed(test=self)


class TestPassed(Parameterizable, Condition):

    test = Parameter(Instance[Test])

    def check(self):
        return bool(self.test.cache.get(self.test.name, limit=1))

    @property
    def invariants(self):
        if not self.test.scenario.idle and self.test.subject.target is not None:
            yield self >> self.test.subject.target


class Stub(Parameterizable, Task):
    """
    A stubbing task used to mimic the behavior of a subject task.

    Runs the $scenario for the $subject.
    Shares its target with the $subject.
    """

    scenario = Parameter(Instance[Scenario])
    subject = Parameter(Instance[Task])

    @routine
    def execute(self):
        yield deferrable(self.scenario.run).defer(self.subject)

    @property
    def target(self):
        return self.subject.target
