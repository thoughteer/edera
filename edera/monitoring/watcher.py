import datetime

import six

import edera.helpers

from edera.exceptions import ExcusableError
from edera.exceptions import MonitorInconsistencyError
from edera.exceptions import StorageOperationError
from edera.flags import InterThreadFlag
from edera.graph import Graph
from edera.helpers import Serializable
from edera.helpers.serializable import IntegerField
from edera.helpers.serializable import MappingField
from edera.helpers.serializable import OptionalField
from edera.helpers.serializable import StringField
from edera.invokers import PersistentInvoker
from edera.linearizers import DFSLinearizer
from edera.monitoring.agent import MonitoringAgent
from edera.monitoring.snapshot import MonitoringSnapshot
from edera.monitoring.snapshot import MonitoringSnapshotCore
from edera.monitoring.snapshot import TaskPayload
from edera.routine import routine


class MonitorWatcher(object):
    """
    A monitor watcher that aggregates snapshot updates and serves as a DAO.

    Attributes:
        monitor (Storage) - the storage to watch
    """

    def __init__(self, monitor):
        """
        Args:
            monitor (Storage) - a storage to watch
        """
        self.monitor = monitor

    def load_task_payload(self, alias):
        """
        Load the last available payload for the task alias.

        Args:
            alias (String)

        Returns:
            Optional[TaskPayload]

        Raises:
            StorageOperationError if something went wrong with the storage
        """
        return self.__load_task_payload(alias)

    def load_snapshot_core(self):
        """
        Load the last available snapshot core.

        Returns:
            Optional[MonitoringSnapshotCore]

        Raises:
            StorageOperationError if something went wrong with the storage
        """
        return self.__load_snapshot_core()

    @routine
    def recover(self):
        """
        Assemble a full snapshot from the last available checkpoint.

        Returns:
            Tuple[MonitorWatcherCheckpoint, MonitoringSnapshot]

        Raises:
            MonitorInconsistencyError if some data is missing from the storage
            StorageOperationError if something went wrong with the storage
        """
        checkpoint = self.__load_checkpoint()
        if checkpoint is None:
            yield (MonitorWatcherCheckpoint(None, {}, None, {}), MonitoringSnapshot.void())
            return
        core = self.__load_snapshot_core(version=checkpoint.core_version)
        payloads = {}
        for alias, payload_version in six.iteritems(checkpoint.payload_versions):
            yield
            payloads[alias] = self.__load_task_payload(alias, version=payload_version)
        yield (checkpoint, MonitoringSnapshot(core, payloads))

    @routine
    def run(self, delay=datetime.timedelta(seconds=3)):
        """
        Run an infinite aggregation cycle.

        Periodically
          - collects new snapshot updates
          - applies them to the snapshot
          - augments the snapshot
          - saves it

        Updates from the same agent will be applied in chronological order.
        Each update will be applied exactly once.

        Args:
            delay (TimeDelta) - a delay between aggregations
                Default is 3 seconds.
        """

        @routine
        def process():

            def control():
                if flag.raised:
                    raise ExcusableError("recovery is needed")

            @routine
            def update():
                try:
                    yield advance.defer(checkpoint, snapshot)
                except Exception as error:
                    flag.up()
                    raise ExcusableError(error)

            flag = InterThreadFlag()
            try:
                checkpoint, snapshot = yield self.recover.defer()
            except StorageOperationError as error:
                raise ExcusableError(error)  # pragma: no cover
            yield PersistentInvoker(update, delay=delay).invoke[control].defer()

        @routine
        def advance(checkpoint, snapshot):
            affected = set()
            next_checkpoint = checkpoint.clone()
            agents = MonitoringAgent.discover(self.monitor)
            for agent in agents:
                yield
                cursor = checkpoint.cursors.get(agent.name)
                for version, update in reversed(agent.pull(since=cursor)):
                    for task in update.apply(snapshot, agent.name):
                        affected.add(snapshot.core.aliases[task])
                    next_checkpoint.cursors[agent.name] = version + 1
            last_checkpoint = self.__load_checkpoint()
            if last_checkpoint and last_checkpoint.version > checkpoint.version:
                raise RuntimeError("snapshot can be no longer valid")  # pragma: no cover
            augment(snapshot)
            yield
            next_checkpoint.core_version = self.monitor.put("core", snapshot.core.serialize())
            for alias in set(affected):
                yield
                payload = snapshot.payloads[alias]
                new_payload_version = self.monitor.put("payload/" + alias, payload.serialize())
                next_checkpoint.payload_versions[alias] = new_payload_version
            next_checkpoint.version = self.monitor.put("checkpoint", next_checkpoint.serialize())
            self.monitor.delete("checkpoint", till=next_checkpoint.version)
            self.monitor.delete("core", till=checkpoint.core_version)
            for alias in set(affected):
                yield
                if alias not in checkpoint.payload_versions:
                    continue
                self.monitor.delete("payload/" + alias, till=checkpoint.payload_versions[alias])
            for agent in agents:
                if agent.name not in checkpoint.cursors:
                    continue
                yield
                agent.drop(till=checkpoint.cursors[agent.name])
            checkpoint.update(next_checkpoint)

        def augment(snapshot):
            graph = Graph()
            for alias in snapshot.core.states:
                graph.add(alias)
            for alias in graph:
                for dependency in (snapshot.payloads[alias].dependencies or ()):
                    graph.link(dependency, alias)
            pending = set()
            for alias in DFSLinearizer().linearize(graph):
                state = snapshot.core.states[alias]
                if state.completed:
                    continue
                dependencies = snapshot.payloads[alias].dependencies or set()
                if not state.phony or dependencies.intersection(pending):
                    pending.add(alias)
                    continue
                state.completed = True
            snapshot.core.timestamp = edera.helpers.now()

        yield PersistentInvoker(process, delay=delay).invoke.defer()

    def __load_checkpoint(self):
        records = self.monitor.get("checkpoint", limit=1)
        if records:
            return MonitorWatcherCheckpoint.deserialize(records[0][0], records[0][1])

    def __load_task_payload(self, alias, version=None):
        arguments = {"limit": 1} if version is None else {"since": version}
        records = self.monitor.get("payload/" + alias, **arguments)
        if version is not None and (not records or records[-1][0] != version):
            raise MonitorInconsistencyError("invalid payload version for %s: %d" % (alias, version))
        return TaskPayload.deserialize(records[-1][1]) if records else None

    def __load_snapshot_core(self, version=None):
        arguments = {"limit": 1} if version is None else {"since": version}
        records = self.monitor.get("core", **arguments)
        if version is not None and (not records or records[-1][0] != version):
            raise MonitorInconsistencyError("invalid snapshot core version: %d" % version)
        return MonitoringSnapshotCore.deserialize(records[-1][1]) if records else None


class MonitorWatcherCheckpoint(Serializable):
    """
    A checkpoint descriptor that contains information needed for recovery.

    Attributes:
        version (Optional[Integer]) - the version of the checkpoint (non-serializable)
        cursors (Mapping[String, Integer]) - the cursors (update versions) by agent name
        core_version (Optional[Integer]) - the version of the snapshot core
            Could be $None if there were no saved snapshots.
        payload_versions (Mapping[String, Integer]) - the payload versions by task alias
    """

    cursors = MappingField(StringField, IntegerField)
    core_version = OptionalField(IntegerField)
    payload_versions = MappingField(StringField, IntegerField)

    def __init__(self, version, cursors, core_version, payload_versions):
        """
        Args:
            version (Optional[Integer])
            cursors (Mapping[String, Integer])
            core_version (Optional[Integer])
            payload_versions (Mapping[String, Integer])
        """
        self.version = version
        self.cursors = cursors
        self.core_version = core_version
        self.payload_versions = payload_versions

    def clone(self):
        """
        Create a deep copy of the checkpoint.

        Returns:
            MonitorWatcherCheckpoint
        """
        return MonitorWatcherCheckpoint(
            self.version, dict(self.cursors), self.core_version, dict(self.payload_versions))

    @classmethod
    def deserialize(cls, version, string):
        result = super(MonitorWatcherCheckpoint, cls).deserialize(string)
        result.version = version
        return result

    def update(self, checkpoint):
        """
        Borrow data from another checkpoint.

        No data is deep-copied.

        Args:
            checkpoint (MonitorWatcherCheckpoint) - a checkpoint to borrow data from
        """
        self.version = checkpoint.version
        self.cursors = checkpoint.cursors
        self.core_version = checkpoint.core_version
        self.payload_versions = checkpoint.payload_versions
