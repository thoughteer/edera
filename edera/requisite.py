import abc

import six


@six.add_metaclass(abc.ABCMeta)
class Requisite(object):
    """
    An interface for task requisites.

    A requisite is a requirement that a task imposes onto the workflow.
    It is essentially an instruction for the workflow builder.

    Attributes:
        priority (Real) - the priority of the requisite
            Defines the order in which requisites are satisfied.
            Default is 0.
    """

    priority = 0

    @abc.abstractmethod
    def satisfy(self, requisitor, workflow):
        """
        Satisfy the requisite within the workflow.

        Adjusts the workflow for the requisitor incrementally.
        May yield a number of other (requisitor, requisite) pairs during the process.
        You must be careful when yielding a requisite of higher priority.

        Args:
            requisitor (Optional[Task]) - a task that requested this operation
            workflow (Graph) - a workflow to operate with

        Returns:
            Optional[Iterable[Tuple[Optional[Task], Requisite]]]
        """
