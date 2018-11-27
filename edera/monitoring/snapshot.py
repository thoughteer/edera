import abc

import six

import edera.helpers

from edera.helpers import Serializable


class MonitoringSnapshot(Serializable):
    """
    A monitoring snapshot that holds general information about the workflow.

    Attributes:
        aliases (Mapping[String, String]) - the aliases by task name
        reports (Mapping[String, TaskReport]) - the task reports by alias
        timestamp (DateTime) - the time the snapshot was last actualized

    See also:
        $MonitoringAgent
        $TaskReport
    """

    def __init__(self, aliases, reports):
        """
        Args:
            aliases (Mapping[String, String]) - aliases by task name
            reports (Mapping[String, TaskReport]) - task reports by alias
        """
        self.aliases = aliases
        self.reports = reports
        self.timestamp = edera.helpers.now()

    def add(self, tasks):
        """
        Add the new tasks to the snapshot.

        Creates initial reports for the tasks.

        Args:
            tasks (Iterable[String]) - task names to add
        """
        for task in tasks:
            alias = edera.helpers.sha1(task)[:10]
            self.aliases[task] = alias
            self.reports[alias] = TaskReport(TaskState(task), TaskPayload())

    @classmethod
    def void(cls):
        """
        Create an empty snapshot.

        Returns:
            MonitoringSnapshot
        """
        return cls({}, {})


class TaskReport(object):
    """
    A task report that holds all the information about a particular task.

    Attributes:
        state (TaskState) - the state of the task (essential information)
        payload (TaskPayload) - auxiliary information associated with the task
            Doesn't get serialized with the snapshot.

    See also:
        $TaskPayload
        $TaskState
    """

    def __getstate__(self):
        return self.state

    def __init__(self, state, payload):
        """
        Args:
            state (TaskState)
            payload (TaskPayload)
        """
        self.state = state
        self.payload = payload

    def __setstate__(self, value):
        self.state = value
        self.payload = TaskPayload()


class TaskState(object):
    """
    A basic task state.

    Attributes:
        name (String) - the task name
        phony (Boolean) - whether the task is "phony"
        completed (Boolean) - whether the task is completed
        runs (Mapping[String, DateTime]) - names of agents in progress (+ timestamps)
        failures (Mapping[String, DateTime]) - names of failed agents (+ last timestamps)
        span (Optional[Tuple[DateTime, DateTime]]) - the start time and the finish time
                of the first successful execution attempt
        dependencies (Set[String]) - the set of aliases of tasks that the task depends on
        announcement (Any) - the announcement provided by the task via annotation
            Should be pickling-friendly.
    """

    def __init__(self, name):
        """
        Args:
            name (String) - a task name
        """
        self.name = name
        self.phony = False
        self.completed = False
        self.runs = {}
        self.failures = {}
        self.span = None
        self.dependencies = set()
        self.announcement = None


class TaskPayload(Serializable):
    """
    A basic task payload.

    Attributes:
        logs (Mapping[String, List[Tuple[DateTime, String]]]) - log messages, grouped by agent name,
                with corresponding timestamps
    """

    def __init__(self):
        self.logs = {}


@six.add_metaclass(abc.ABCMeta)
class MonitoringSnapshotUpdate(Serializable):
    """
    A monitoring snapshot update.

    Updates enrich the current snapshot with additional information.
    """

    @abc.abstractmethod
    def apply(self, snapshot, agent):
        """
        Apply the update to the snapshot on behalf of the monitoring agent.

        Args:
            snapshot (MonitoringSnapshot) - a snapshot to update
            agent (MonitoringAgent) - an agent that caused the update

        Returns:
            Iterable[String] - names of tasks the payload of which was affected
        """


class WorkflowUpdate(MonitoringSnapshotUpdate):
    """
    An update that adds information on task dependencies and "phony" flags to the snapshot.

    It also publishes all the announcements.

    Attributes:
        dependencies (Mapping[String, Set[String]]) - the dependencies grouped by task name
        phonies (Set[String]) - the names of "phony" tasks
        announcements (Mapping[String, Any]) - the announcements by task name
    """

    def __init__(self, dependencies, phonies, announcements):
        """
        Args:
            dependencies (Mapping[String, Set[String]]) - dependencies grouped by task name
            phonies (Set[String]) - names of "phony" tasks
            announcements (Mapping[String, Any]) - announcements by task name
        """
        self.dependencies = dependencies
        self.phonies = phonies
        self.announcements = announcements

    def apply(self, snapshot, agent):
        snapshot.add(task for task in self.dependencies if task not in snapshot.aliases)
        for task in self.dependencies:
            state = snapshot.reports[snapshot.aliases[task]].state
            state.phony = task in self.phonies
            state.announcement = self.announcements.get(task)
            state.dependencies |= {
                snapshot.aliases[dependency]
                for dependency in self.dependencies[task]
            }
        return []


class TaskStatusUpdate(MonitoringSnapshotUpdate):
    """
    An update that changes the status of a task.

    Attributes:
        task (String) - the task name
        status (String) - "running", "stopped", "failed", or "completed"
        timestamp (DateTime) - the timestamp of the update
    """

    def __init__(self, task, status, timestamp):
        """
        Args:
            task (String) - a task name
            status (String) - "running", "stopped", "failed", or "completed"
            timestamp (DateTime) - a timestamp of the update
        """
        self.task = task
        self.status = status
        self.timestamp = timestamp

    def apply(self, snapshot, agent):
        state = snapshot.reports[snapshot.aliases[self.task]].state
        if self.status == "completed":
            state.completed = True
            if agent.name in state.runs:
                if state.span is None or state.span[0] > state.runs[agent.name]:
                    state.span = (state.runs[agent.name], self.timestamp)
        elif self.status == "failed":
            state.failures[agent.name] = self.timestamp
        if self.status == "running":
            state.runs[agent.name] = self.timestamp
        elif agent.name in state.runs:
            del state.runs[agent.name]
        return []


class TaskLogUpdate(MonitoringSnapshotUpdate):
    """
    An update that appends messages to the log of a task.

    Attributes:
        task (String) - the task name
        message (String) - the message to append
        timestamp (DateTime) - the timestamp of the update

    Constants:
        LIMIT (Integer) - the maximum number of last messages to store (per agent)
    """

    LIMIT = 10

    def __init__(self, task, message, timestamp):
        """
        Args:
            task (String) - a task name
            message (String) - a message to append
            timestamp (DateTime) - a timestamp of the update
        """
        self.task = task
        self.message = message
        self.timestamp = timestamp

    def apply(self, snapshot, agent):
        logs = snapshot.reports[snapshot.aliases[self.task]].payload.logs
        if agent.name not in logs:
            logs[agent.name] = []
        log = logs[agent.name]
        log.insert(0, (self.timestamp, self.message))
        if len(log) > self.LIMIT:
            log.pop()
        yield self.task
