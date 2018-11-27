import abc

import six


@six.add_metaclass(abc.ABCMeta)
class WorkflowProcessor(object):
    """
    An interface for a workflow processor.

    Workflow processors modify the workflow without checking targets or executing tasks.
    """

    @abc.abstractmethod
    def process(self, workflow):
        """
        Process the workflow in-place.

        Args:
            workflow (Graph)
        """
