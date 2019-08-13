import abc

import edera.helpers

from edera.helpers import AbstractSerializable
from edera.helpers import Serializable
from edera.helpers.serializable import BooleanField
from edera.helpers.serializable import DateTimeField
from edera.helpers.serializable import GenericField
from edera.helpers.serializable import ListField
from edera.helpers.serializable import MappingField
from edera.helpers.serializable import OptionalField
from edera.helpers.serializable import SetField
from edera.helpers.serializable import StringField
from edera.helpers.serializable import TupleField


class MonitoringSnapshot(object):
    """
    A monitoring snapshot that holds important information about the workflow.

    Attributes:
        core (MonitoringSnapshotCore)
        payloads (Mapping[String, TaskPayload]) - the task payloads by alias

    See also:
        $MonitoringAgent
        $MonitoringSnapshotCore
        $TaskPayload
    """

    def __contains__(self, task):
        """
        Check whether the task has been already added to the snapshot.

        Args:
            task (String) - a task name to look for

        Returns:
            Boolean - True iff the task has been already added to the snapshot
        """
        return task in self.core.aliases

    def __init__(self, core, payloads):
        """
        Args:
            core (MonitoringSnapshotCore)
            payloads (Mapping[String, TaskPayload]) - task payloads by alias
        """
        self.core = core
        self.payloads = payloads

    def add(self, tasks):
        """
        Add the new tasks to the snapshot.

        Updates the core and creates empty payloads for the tasks.

        Args:
            tasks (List[String]) - task names to add
        """
        self.core.add(tasks)
        for task in tasks:
            self.payloads[self.core.aliases[task]] = TaskPayload()

    @classmethod
    def void(cls):
        """
        Create an empty snapshot.

        Returns:
            MonitoringSnapshot
        """
        return cls(MonitoringSnapshotCore({}, {}), {})


class TaskState(Serializable):
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
        baggage (Any) - the baggage provided by the task via annotation
            Should be serializable.
    """

    name = StringField
    phony = BooleanField
    completed = BooleanField
    runs = MappingField(StringField, DateTimeField)
    failures = MappingField(StringField, DateTimeField)
    span = OptionalField(TupleField(DateTimeField, DateTimeField))
    baggage = MappingField(StringField, StringField)

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
        self.baggage = {}


class MonitoringSnapshotCore(Serializable):
    """
    A monitoring snapshot core that holds basic information about the workflow.

    Attributes:
        aliases (Mapping[String, String]) - the aliases by task name
        states (Mapping[String, TaskState]) - the task states by alias
        timestamp (DateTime) - the time the snapshot was last actualized

    See also:
        $TaskState
    """

    aliases = MappingField(StringField, StringField)
    states = MappingField(StringField, GenericField(TaskState))

    def __init__(self, aliases, states):
        """
        Args:
            aliases (Mapping[String, String]) - aliases by task name
            states (Mapping[String, TaskState]) - task states by alias
        """
        self.aliases = aliases
        self.states = states
        self.timestamp = edera.helpers.now()

    def add(self, tasks):
        """
        Add the new tasks to the snapshot core.

        Creates aliases and initial states for the tasks.

        Args:
            tasks (Iterable[String]) - task names to add
        """
        for task in tasks:
            alias = edera.helpers.sha1(task)[:10]
            self.aliases[task] = alias
            self.states[alias] = TaskState(task)


class TaskPayload(Serializable):
    """
    A basic task payload.

    Attributes:
        dependencies (Optional[Set[String]]) - the set of aliases of tasks that the task depends on
        logs (Mapping[String, List[Tuple[DateTime, String]]]) - log messages, grouped by agent name,
                with corresponding timestamps
    """

    dependencies = OptionalField(SetField(StringField))
    logs = MappingField(StringField, ListField(TupleField(DateTimeField, StringField)))

    def __init__(self):
        self.dependencies = None
        self.logs = {}


class MonitoringSnapshotUpdate(AbstractSerializable):
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

    It also publishes all the baggages.

    Attributes:
        dependencies (Mapping[String, Set[String]]) - the dependencies grouped by task name
        phonies (Set[String]) - the names of "phony" tasks
        baggages (Mapping[String, Any]) - the baggages by task name
    """

    dependencies = MappingField(StringField, SetField(StringField))
    phonies = SetField(StringField)
    baggages = MappingField(StringField, MappingField(StringField, StringField))

    def __init__(self, dependencies, phonies, baggages):
        """
        Args:
            dependencies (Mapping[String, Set[String]]) - dependencies grouped by task name
            phonies (Set[String]) - names of "phony" tasks
            baggages (Mapping[String, Any]) - baggages by task name
        """
        self.dependencies = dependencies
        self.phonies = phonies
        self.baggages = baggages

    def apply(self, snapshot, agent):
        snapshot.add([task for task in self.dependencies if task not in snapshot])
        for task in self.dependencies:
            alias = snapshot.core.aliases[task]
            state = snapshot.core.states[alias]
            state.phony = task in self.phonies
            state.baggage = self.baggages.get(task)
            if agent.name in state.runs:
                del state.runs[agent.name]
            payload = snapshot.payloads[alias]
            if payload.dependencies is None:
                payload.dependencies = {
                    snapshot.core.aliases[dependency]
                    for dependency in self.dependencies[task]
                }
                yield task


class TaskStatusUpdate(MonitoringSnapshotUpdate):
    """
    An update that changes the status of a task.

    Attributes:
        task (String) - the task name
        status (String) - "running", "stopped", "failed", or "completed"
        timestamp (DateTime) - the timestamp of the update
    """

    task = StringField
    status = StringField
    timestamp = DateTimeField

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
        if self.task not in snapshot:
            snapshot.add([self.task])
        state = snapshot.core.states[snapshot.core.aliases[self.task]]
        if self.status == "completed":
            state.completed = True
            if agent.name in state.runs:
                assert state.runs[agent.name] <= self.timestamp
                if state.span is None or state.span[1] > self.timestamp:
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

    task = StringField
    message = StringField
    timestamp = DateTimeField

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
        if self.task not in snapshot:
            snapshot.add([self.task])
        logs = snapshot.payloads[snapshot.core.aliases[self.task]].logs
        if agent.name not in logs:
            logs[agent.name] = []
        log = logs[agent.name]
        log.insert(0, (self.timestamp, self.message))
        if len(log) > self.LIMIT:
            log.pop()
        yield self.task
