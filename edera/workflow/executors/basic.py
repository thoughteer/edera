import logging

from edera.exceptions import ExcusableError
from edera.exceptions import ExcusableWorkflowExecutionError
from edera.exceptions import WorkflowExecutionError
from edera.helpers import Phony
from edera.queue import Queue
from edera.routine import deferrable
from edera.routine import routine
from edera.workflow.executor import WorkflowExecutor


class BasicWorkflowExecutor(WorkflowExecutor):
    """
    A basic workflow executor.

    Expects tasks to be ranked in advance.
    Runs tasks in the current thread one by one, handles exceptions, and performs logging.

    This executor is interruptible.

    See also:
        $TaskRanker
    """

    @routine
    def execute(self, workflow):
        queue = Queue(workflow)
        stopped_tasks = []
        failed_tasks = []
        while queue:
            task = queue.pick()
            if task.execute is Phony:
                queue.accept()
                continue
            try:
                logging.getLogger(__name__).debug("Picked task %r", task)
                if task.target is not None:
                    completed = yield deferrable(task.target.check).defer()
                    if completed:
                        queue.accept()
                        continue
                logging.getLogger(__name__).info("Running task %r", task)
                yield deferrable(task.execute).defer()
            except ExcusableError as error:
                logging.getLogger(__name__).info("Task %r stopped: %s", task, error)
                stopped_tasks.append(task)
                queue.discard()
            except Exception:
                logging.getLogger(__name__).exception("Task %r failed:", task)
                failed_tasks.append(task)
                queue.discard()
            else:
                logging.getLogger(__name__).info("Task %r completed", task)
                queue.accept()
        if failed_tasks:
            raise WorkflowExecutionError(failed_tasks)
        if stopped_tasks:
            raise ExcusableWorkflowExecutionError(stopped_tasks)
