import abc

import six

from edera.qualifiers import DateTime
from edera.requisites import shortcut
from edera.task import Task
from edera.testing.selectors import AllTestSelector
from edera.workflow.processors import TaskSegregator
from edera.workflow.processors import WorkflowTestifier


@six.add_metaclass(abc.ABCMeta)
class DaemonAutoTester(object):
    """
    A daemon auto-tester.

    Incapsulates information needed for auto-testing.

    Attributes:
        box (Box) - the box that will keep the current test group color
        cache (Storage) - the storage used to mark passed tests
        selector (TestSelector)
        timestamps (Iterable[DateTime]) - the set of timestamps used for seeding
    """

    @abc.abstractproperty
    def box(self):
        pass

    @abc.abstractproperty
    def cache(self):
        pass

    def seed(self, seeder):
        """
        Get an auto-testing task.

        Uses the provided seeding function to instantiate roots for each of the $timestamps.

        Args:
            seeder (Callable[[DateTime], Task]) - a seeding function

        Returns:
            Task
        """

        class AutoTest(Task):

            @shortcut
            def requisite(self):
                for timestamp in timestamps:
                    yield seeder(timestamp)

        timestamps = self.timestamps
        return AutoTest()

    @property
    def selector(self):
        return AllTestSelector()

    def testify(self, workflow):
        """
        Make the given workflow test itself.

        Args:
            workflow (Graph)

        See also:
            $TaskSegregator
            $WorkflowTestifier
        """
        WorkflowTestifier(self.cache, selector=self.selector).process(workflow)
        TaskSegregator(self.box).process(workflow)

    @property
    def timestamps(self):
        yield DateTime.qualify("1991-07-26T09:00:00Z")[0]
