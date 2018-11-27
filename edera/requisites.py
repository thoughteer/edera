import collections
import inspect

import six

from edera.exceptions import RequisiteConformationError
from edera.requisite import Requisite
from edera.task import Task


class Annotate(Requisite):
    """
    A requisite that annotates the requisitor.
    """

    priority = -1

    def __init__(self, key, value):
        """
        Args:
            key (String)
            value (Any)

        See also:
            $GraphNode
        """
        self.key = key
        self.value = value

    def satisfy(self, requisitor, workflow):
        assert self.key not in workflow[requisitor].annotation
        workflow[requisitor][self.key] = self.value


class Assign(Requisite):
    """
    A requisite that alters the requisitor (assigns some requisite to another task).

    Includes the assignee into the workflow automatically.
    """

    priority = -1

    def __init__(self, task, requisite):
        """
        Args:
            task (Task) - an assignee
            requisite (Requisite) - a requisite to assign
        """
        self.task = task
        self.requisite = requisite

    def satisfy(self, requisitor, workflow):
        yield (None, Include(self.task))
        yield (self.task, self.requisite)


class Follow(Requisite):
    """
    A requisite that adds a link from some task to the requisitor.

    Includes the task into the workflow automatically.

    The requisitor must not be $None.
    """

    priority = -2

    def __init__(self, task):
        """
        Args:
            task (Task)
        """
        self.task = task

    def satisfy(self, requisitor, workflow):
        assert requisitor is not None
        yield (None, Include(self.task))
        workflow.link(self.task, requisitor)


class Include(Requisite):
    """
    A requisite that includes some task into the workflow.

    Recursively satisfies the requisite of the new task.
    Collects all requisites along the MRO.
    """

    def __init__(self, task):
        """
        Args:
            task (Task)
        """
        self.task = task

    def satisfy(self, requisitor, workflow):
        if self.task not in workflow:
            workflow.add(self.task)
            requisites = [
                base.requisite.fget(self.task)
                for base in inspect.getmro(self.task.__class__)
                if issubclass(base, Task) and "requisite" in base.__dict__
            ]
            yield (self.task, SatisfyAll(requisites))


class SatisfyAll(Requisite):
    """
    A requisite that attempts to satisfy other requisites.

    This is a helper class that allows to treat requisite collections as requisites.
    It preserves the requisitor.
    """

    def __init__(self, requisites):
        """
        Args:
            requisites (Iterable[Requisite])
        """
        self.requisites = requisites

    def satisfy(self, requisitor, workflow):
        for requisite in self.requisites:
            yield (requisitor, requisite)


def conform(requisite):
    """
    Get the canonical form of the requisite from a shortcut.

    Converts:
      - a mapping to a series of $Assign's
            Keys - assignees, values - assignments.
      - an iterable object to a corresponding $SatisfyAll
      - a task to a corresponding $Follow
            This is the most convenient way to define dependencies.

    Args:
        requisite (Any) - an object to convert to a requisite

    Returns:
        Requisite

    Raises:
        RequisiteConformationError if $requisite cannot be converted to a requisite
    """
    if isinstance(requisite, collections.Mapping):
        assignments = [
            Assign(task, conform(assignment))
            for task, assignment in six.iteritems(requisite)
        ]
        return SatisfyAll(assignments)
    if isinstance(requisite, collections.Iterable):
        return SatisfyAll(list(map(conform, requisite)))
    if isinstance(requisite, Task):
        return Follow(requisite)
    if requisite is not None and not isinstance(requisite, Requisite):
        raise RequisiteConformationError(requisite)
    return requisite


def shortcut(evaluator):
    """
    Create an auto-conforming requisite property.

    Allows you to write shorter requisite declarations.

    Args:
        evaluator (Callable[[Any], Any]) - a requisite property evaluator

    Returns:
        Property - auto-conforming requisite property
    """

    @six.wraps(evaluator)
    def conformer(self):
        return conform(evaluator(self))

    return property(conformer)
