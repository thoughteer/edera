from edera.qualifiers import DateTime
from edera.requisites import shortcut
from edera.task import Task
from edera.testing.selectors import AllTestSelector
from edera.workflow.processors import TaskSegregator
from edera.workflow.processors import WorkflowTestifier


DEFAULT_TIMESTAMP = DateTime.qualify("1991-07-26T09:00:00Z")[0]


class DaemonAutoTester(object):
    """
    A daemon auto-tester.

    Incapsulates information needed for auto-testing.

    Attributes:
        box (Box) - the box that will keep the current test group color
        registry (Storage) - the storage used to mark passed tests
        selector (TestSelector)
        timestamps (Iterable[DateTime]) - the set of timestamps used for seeding
    """

    def __init__(self, box, registry, selector=AllTestSelector(), timestamps=[DEFAULT_TIMESTAMP]):
        """
        Args:
            box (Box) - a box that will keep the current test group color
            registry (Storage) - a storage to use to mark passed tests
            selector (TestSelector)
                Default is an instance of $AllTestSelector.
            timestamps (Iterable[DateTime]) - a set of timestamps to use for seeding
                Default is a single $DEFAULT_TIMESTAMP.
        """
        self.box = box
        self.registry = registry
        self.selector = selector
        self.timestamps = timestamps

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

    def testify(self, workflow):
        """
        Make the given workflow test itself.

        Args:
            workflow (Graph)

        See also:
            $TaskSegregator
            $WorkflowTestifier
        """
        WorkflowTestifier(self.registry, selector=self.selector).process(workflow)
        TaskSegregator(self.box).process(workflow)
