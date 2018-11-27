import abc

import six


@six.add_metaclass(abc.ABCMeta)
class WorkflowExecutor(object):
    """
    An interface for a workflow executor.

    A workflow executor runs all tasks in a given graph.
    """

    @abc.abstractmethod
    def execute(self, workflow):
        """
        Run tasks in the graph.

        Args:
            workflow (Graph) - a graph of tasks to execute

        Raises:
            ExcusableError if something went wrong
            Exception if something went surprisingly wrong
        """
