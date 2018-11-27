import abc

from edera.exceptions import TargetVerificationError
from edera.nameable import Nameable
from edera.parameterizable import Parameterizable
from edera.parameterizable import Parameter
from edera.qualifiers import Instance
from edera.qualifiers import Mapping
from edera.routine import deferrable
from edera.routine import routine
from edera.task import Task


class Scenario(Nameable):
    """
    An interface for a set of instructions used for testing purposes.

    Scenarios are applied to tasks (called "subjects") in order to change their behavior
    for testing purposes, e.g. to emulate them or to check something after execution.

    Scenarios may or may not interfere with the environment.
    For example, a test might check that the subject raises an exception in response to
    some invalid input.
    In this case, the target of the subject should be ignored.
    You should denote this explicitly by setting $idle to $True.

    Attributes:
        idle (Boolean) - whether the target of the subject should be ignored
            Default is $False.
    """

    idle = False

    @property
    def name(self):
        return self.__class__.__name__

    @abc.abstractmethod
    def run(self, subject):
        """
        Run the scenario for the subject task.

        Args:
            subject (Task)
        """

    @abc.abstractmethod
    def stub(self, subject, dependencies):
        """
        Define stubbing scenarios for all the dependencies of the subject task.

        Args:
            subject (Task)
            dependencies (Iterable[Task])

        Returns:
            Mapping[Task, Scenario]
                Just omit a dependency in order to ignore it.
        """


class ScenarioWithProvidedStubs(Parameterizable, Scenario):
    """
    An abstract scenario that uses externally provided stubbing scenarios $stubs.
    """

    stubs = Parameter(Mapping[Instance[Task], Instance[Scenario]])

    def stub(self, subject, dependencies):
        return self.stubs


class DefaultScenario(Scenario):
    """
    The most simple implementation of a scenario.

    Executes the subject itself, assuming the same stubbing scenario for all its dependencies,
    and checks its target after that.
    """

    @routine
    def run(self, subject):
        yield deferrable(subject.execute).defer()
        if subject.target is not None:
            completed = yield deferrable(subject.target.check).defer()
            if not completed:
                raise TargetVerificationError(subject)

    def stub(self, subject, dependencies):
        return {dependency: DefaultScenario() for dependency in dependencies}
