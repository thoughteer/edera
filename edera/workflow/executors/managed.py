from edera.routine import deferrable
from edera.routine import routine
from edera.workflow.executor import WorkflowExecutor


class ManagedWorkflowExecutor(WorkflowExecutor):
    """
    A workflow executor that encloses the execution procedure in a context manager.

    See also:
        $edera.managers
    """

    def __init__(self, base, manager):
        """
        Args:
            base (WorkflowExecutor) - a base workflow executor
            manager (ContextManager) - a workflow execution context manager
        """
        self.__base = base
        self.__manager = manager

    @routine
    def execute(self, workflow):
        with self.__manager:
            yield deferrable(self.__base.execute).defer(workflow)
