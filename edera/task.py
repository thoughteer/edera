from edera.helpers import phony
from edera.nameable import Nameable


class Task(Nameable):
    """
    An interface for tasks.

    Tasks are the central objects of the whole framework.
    They serve as building blocks for workflows that get executed.

    Attributes:
        requisite (Optional[Requisite]) - the requisite of the task
            Default is $None.
        target (Optional[Condition]) - the completeness condition of the task
            Must resolve to $True on check iff the task is complete.
            Default is $None, which means the developer is responsible for the consequences
            of multiple $execute calls.
    """

    @phony
    def execute(self):
        """
        Execute the task.

        Does nothing by default.

        Raises:
            ExcusableError if you need to stop the task intentionally
            SystemExit if you need to stop the whole workflow execution silently
        """

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def requisite(self):
        pass

    @property
    def target(self):
        pass

    def unwrap(self):
        """
        Unwrap the task if it has been wrapped.

        Returns:
            Task
        """
        return self


class TaskWrapper(Task):
    """
    A task wrapper.

    Delegates all its method calls to the base task object.
    Allows you to override (wrap) any subset of task methods/properties.
    """

    def __init__(self, base):
        """
        Args:
            base (Task) - a base task
        """
        self.__base = base

    @property
    def execute(self):
        return self.__base.execute

    @property
    def name(self):
        return self.__base.name

    @property
    def requisite(self):
        return self.__base.requisite

    @property
    def target(self):
        return self.__base.target

    def unwrap(self):
        return self.__base
