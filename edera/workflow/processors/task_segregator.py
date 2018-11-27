from edera.condition import ConditionWrapper
from edera.helpers import Phony
from edera.routine import deferrable
from edera.routine import routine
from edera.task import TaskWrapper
from edera.workflow.processor import WorkflowProcessor


class TaskSegregator(WorkflowProcessor):
    """
    A workflow processor that uses "color" annotations to separate environments for tasks.

    Right before each task execution and target check the corresponding color is stored
    in the provided box (or $None if the task has no color).
    This allows you to reconfigure your code to work within a color-dependent environment.

    Empties the box afterwards.

    Usually, this processor is used to isolate conflicting tests/stubs during auto-testing.

    WARNING!
        In order for it to work correctly, task parameters must not depend on the environment;
        employ environment-dependent stuff only during task execution and target checking.
        Also note, that this processor should be applied before, say, $WorkflowTrimmer, which
        performs target checks.
    """

    def __init__(self, box):
        """
        Args:
            box (Box) - an empty box that will store the current color
        """
        self.__box = box

    def process(self, workflow):
        for task in workflow:
            if task is Phony:
                pass
            color = workflow[task].annotation.get("color")
            workflow.replace(SegregatingTaskWrapper(task, color, self.__box))


class SegregatingTaskWrapper(TaskWrapper):
    """
    A task wrapper that puts the given color to the given box before execution.

    Empties the box afterwards.

    It also segregates the target.
    """

    def __init__(self, base, color, box):
        """
        Args:
            base (Task) - a base task
            color (String)
            box (Box)
        """
        TaskWrapper.__init__(self, base)
        self.__color = color
        self.__box = box

    @routine
    def execute(self):
        assert self.__box.get() is None
        self.__box.put(self.__color)
        try:
            yield deferrable(super(SegregatingTaskWrapper, self).execute).defer()
        finally:
            self.__box.put(None)

    @property
    def target(self):
        base = super(SegregatingTaskWrapper, self).target
        if base is None:
            return None
        return SegregatingConditionWrapper(base, self.__color, self.__box)


class SegregatingConditionWrapper(ConditionWrapper):
    """
    A condition wrapper that puts the given color to the given box before checking.

    Empties the box afterwards.
    """

    def __init__(self, base, color, box):
        """
        Args:
            base (Condition) - a base condition
            color (String)
            box (Box)
        """
        ConditionWrapper.__init__(self, base)
        self.__color = color
        self.__box = box

    @routine
    def check(self):
        assert self.__box.get() is None
        self.__box.put(self.__color)
        try:
            result = yield deferrable(super(SegregatingConditionWrapper, self).check).defer()
            yield result
        finally:
            self.__box.put(None)
