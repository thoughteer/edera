from edera.task import TaskWrapper
from edera.workflow.processor import WorkflowProcessor


class TaskFreezer(WorkflowProcessor):
    """
    A workflow processor that pre-computes properties of all tasks.
    """

    def process(self, workflow):
        for task in workflow:
            workflow.replace(FreezingTaskWrapper(task))


class FreezingTaskWrapper(TaskWrapper):
    """
    A task wrapper that pre-computes all task properties.
    """

    def __init__(self, base):
        TaskWrapper.__init__(self, base)
        self.__name = base.name
        self.__requisite = base.requisite
        self.__target = base.target

    @property
    def name(self):
        return self.__name

    @property
    def requisite(self):
        return self.__requisite

    @property
    def target(self):
        return self.__target
