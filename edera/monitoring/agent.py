import logging
import threading
import traceback
import sys

import edera.helpers

from edera.condition import ConditionWrapper
from edera.exceptions import ConsumptionError
from edera.exceptions import ExcusableError
from edera.exceptions import StorageOperationError
from edera.helpers import CurrentException
from edera.helpers import Phony
from edera.monitoring.snapshot import MonitoringSnapshotUpdate
from edera.monitoring.snapshot import TaskLogUpdate
from edera.monitoring.snapshot import TaskStatusUpdate
from edera.monitoring.snapshot import WorkflowUpdate
from edera.nameable import Nameable
from edera.routine import deferrable
from edera.routine import routine
from edera.task import TaskWrapper


class MonitoringAgent(Nameable):
    """
    A monitoring agent.

    Agents are used to push updates into a storage during workflow execution.
    They are also used to retrieve updates from the storage.

    Agents (unless they are read-only) use a consumer to push updates.
    This allows features like buffering to be implemented naturally.

    Default agents:
      - track the topology of the task graph
      - publish task baggages
      - report statuses of the tasks
      - collect logs during task execution

    Attributes:
        readonly (Boolean) - True iff the agent does not have a consumer to push through

    See also:
        $MonitoringWorkflowExecutor
        $MonitorWatcher
    """

    def __init__(self, name, monitor, consumer=None):
        """
        Args:
            name (String) - a unique name for the agent
            monitor (Storage) - a storage used to store all relevant information
            consumer (Optional[Consumer]) - a consumer that accepts key-value pairs
                We presume that this consumer puts records to the same $monitor.
        """
        self.__name = name
        self.__monitor = monitor
        self.__consumer = consumer
        self.__key = "update/" + name

    @classmethod
    def discover(cls, monitor):
        """
        Get the set of all agents registered in the monitor.

        All discovered agents are read-only.

        Args:
            monitor (Storage) - a storage to search for agents

        Returns:
            Set[MonitoringAgent] - registered agents

        Raises:
            StorageOperationError if something went wrong with the storage
        """
        records = monitor.get("agent")
        result = {cls(name, monitor) for _, name in records}
        if result:
            for agent in result:
                monitor.put("agent", agent.name)
            monitor.delete("agent", till=(records[0][0] + 1))
        return result

    def drop(self, till=None):
        """
        Delete all updates pushed by this agent till the given version (excluding).

        Args:
            till (Optional[Integer])

        Raises:
            StorageOperationError if something went wrong with the storage
        """
        self.__monitor.delete(self.__key, till=till)

    def embrace(self, workflow):
        """
        Take control over the workflow execution.

        Args:
            workflow (Graph) - a task graph to be executed

        Returns:
            Graph - an altered task graph
        """
        self.register()
        dependencies = {
            task.name: {parent.name for parent in workflow[task].parents}
            for task in workflow
        }
        phonies = {task.name for task in workflow if task.execute is Phony}
        baggages = {
            task.name: workflow[task].annotation.get("baggage", {})
            for task in workflow
        }
        self.push(WorkflowUpdate(dependencies, phonies, baggages))
        result = workflow.clone()
        for task in result:
            if task.execute is Phony:
                continue
            task = StatusReportingTaskWrapper(task, self)
            task = LogCapturingTaskWrapper(task, self)
            result.replace(task)
        return result

    @property
    def name(self):
        return self.__name

    def pull(self, since=None):
        """
        Get updates from the monitor pushed there by this agent.

        Args:
            since (Optional[Integer]) - a version to start from (including)
                Default is $None - get all updates.

        Returns:
            List[Tuple[Integer, MonitoringSnapshotUpdate]] - the list of versioned updates

        Raises:
            StorageOperationError if something went wrong with the storage
        """
        return [
            (version, MonitoringSnapshotUpdate.deserialize(serialized_update))
            for version, serialized_update in self.__monitor.get(self.__key, since=since)
        ]

    def push(self, update):
        """
        Put the update to the monitor.

        Args:
            update (MonitoringSnapshotUpdate) - an update to push

        Raises:
            AssertionError if the agent is read-only
        """
        self.__push(self.__key, update.serialize())

    @property
    def readonly(self):
        return self.__consumer is None

    def register(self):
        """
        Register the agent in the monitor.

        Raises:
            AssertionError if the agent is read-only
        """
        self.__push("agent", self.name)

    def __push(self, key, value):
        assert not self.readonly
        try:
            self.__consumer.push((key, value))
        except ConsumptionError:
            logging.getLogger(__name__).warning("Consumer rejected a monitoring record")


class StatusReportingTaskWrapper(TaskWrapper):
    """
    A task wrapper that makes tasks report their status.

    It also saves exception tracebacks to the log.

    There are 4 supported statuses:
      - running (is executed right now)
      - stopped (there was an excusable Exception during the execution)
      - failed (there was an inexcusable Exception during the execution)
      - completed (the execution finished smoothly)

    All storage operation errors are just ignored.

    See also:
        $TaskLogUpdate
        $TaskStatusUpdate
    """

    def __init__(self, base, agent):
        """
        Args:
            base (Task) - a base task
            agent (MonitoringAgent) - an agent to use for pushing updates
        """
        TaskWrapper.__init__(self, base)
        self.__agent = agent

    @routine
    def execute(self):
        self.__report_status("running")
        try:
            yield deferrable(super(StatusReportingTaskWrapper, self).execute).defer()
        except (ExcusableError, SystemExit):
            error = CurrentException()
            self.__report_status("stopped")
            error.reraise()
        except Exception:
            error = CurrentException()
            self.__save_traceback()
            self.__report_status("failed")
            error.reraise()
        else:
            self.__report_status("completed")

    @property
    def target(self):
        condition = super(StatusReportingTaskWrapper, self).target
        if condition is not None:
            return StatusReportingConditionWrapper(condition, self, self.__agent)

    def __report_status(self, status):
        self.__agent.push(TaskStatusUpdate(self.name, status, edera.helpers.now()))

    def __save_traceback(self):
        self.__agent.push(TaskLogUpdate(self.name, _format_traceback(), edera.helpers.now()))


class StatusReportingConditionWrapper(ConditionWrapper):
    """
    A condition wrapper that reports the task status.

    See also:
        $StatusReportingTaskWrapper
    """

    def __init__(self, base, task, agent):
        """
        Args:
            base (Condition) - a base condition
            task (Task) - a host task
            agent (MonitoringAgent) - an agent to use for pushing updates
        """
        ConditionWrapper.__init__(self, base)
        self.__task = task
        self.__agent = agent

    @routine
    def check(self):
        try:
            result = yield deferrable(super(StatusReportingConditionWrapper, self).check).defer()
        except (ExcusableError, SystemExit):
            raise
        except Exception:
            error = CurrentException()
            self.__save_traceback()
            self.__report_status("failed")
            error.reraise()
        if result:
            self.__report_status("completed")
        yield result

    def __report_status(self, status):
        self.__agent.push(TaskStatusUpdate(self.__task.name, status, edera.helpers.now()))

    def __save_traceback(self):
        self.__agent.push(TaskLogUpdate(self.__task.name, _format_traceback(), edera.helpers.now()))


class LogCapturingTaskWrapper(TaskWrapper):
    """
    A task wrapper that captures log messages sent to `edera.monitoring.sink` during execution.

    See also:
        $TaskLogUpdate
    """

    class LogCapturingHandler(logging.Handler):

        def __init__(self, thread, task, agent):
            logging.Handler.__init__(self)
            self.setFormatter(logging.Formatter("%(message)s"))
            self.__thread = thread
            self.__task = task
            self.__agent = agent

        def emit(self, record):
            if threading.current_thread() != self.__thread:
                return
            message = self.format(record)
            self.__agent.push(TaskLogUpdate(self.__task, message, edera.helpers.now()))

    def __init__(self, base, agent):
        """
        Args:
            base (Task) - a base task
            agent (MonitoringAgent) - an agent to use for pushing updates
        """
        TaskWrapper.__init__(self, base)
        self.__agent = agent

    @routine
    def execute(self):
        sink = logging.getLogger("edera.monitoring.sink")
        handler = self.LogCapturingHandler(threading.current_thread(), self.name, self.__agent)
        sink.addHandler(handler)
        try:
            yield deferrable(super(LogCapturingTaskWrapper, self).execute).defer()
        finally:
            sink.removeHandler(handler)


def _format_traceback():
    exception_type, exception_value, exception_traceback = sys.exc_info()
    return "Traceback:\n%s%s" % (
        traceback.format_tb(exception_traceback)[-1],
        "".join(traceback.format_exception_only(exception_type, exception_value)).rstrip(),
    )
