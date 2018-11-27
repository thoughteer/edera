import abc

import six

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
    """

    @abc.abstractproperty
    def box(self):
        pass

    @abc.abstractproperty
    def cache(self):
        pass

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
