import datetime

import six

import edera.helpers

from edera.exceptions import MonitorInconsistencyError
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
        """
        checkpoint = self.__load_checkpoint()
        if checkpoint is None:
            yield (MonitorWatcherCheckpoint({}, None, {}), MonitoringSnapshot.void())
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
        Run the aggregation cycle.

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
        def aggregate():
            agents = MonitoringAgent.discover(self.monitor)
            for agent in agents:
                yield
                cursor = checkpoint.cursors.get(agent.name)
                for version, update in reversed(agent.pull(since=cursor)):
                    for task in update.apply(snapshot, agent):
                        affected.add(snapshot.core.aliases[task])
                    checkpoint.cursors[agent.name] = version + 1
            augment()
            yield
            checkpoint.core_version = self.monitor.put("core", snapshot.core.serialize())
            for alias in set(affected):
                yield
                payload = snapshot.payloads[alias]
                new_payload_version = self.monitor.put("payload/" + alias, payload.serialize())
                affected.remove(alias)
                commited.add(alias)
                checkpoint.payload_versions[alias] = new_payload_version
            new_checkpoint_version = self.monitor.put("checkpoint", checkpoint.serialize())
            self.monitor.delete("checkpoint", till=new_checkpoint_version)
            self.monitor.delete("core", till=checkpoint.core_version)
            for alias in set(commited):
                yield
                self.monitor.delete("payload/" + alias, till=checkpoint.payload_versions[alias])
                commited.remove(alias)
            for agent in agents:
                if agent.name not in checkpoint.cursors:
                    continue
                yield
                agent.drop(till=checkpoint.cursors[agent.name])

        def augment():
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
            snapshot.timestamp = edera.helpers.now()

        checkpoint, snapshot = yield self.recover.defer()
        affected = set()
        commited = set()
        yield PersistentInvoker(aggregate, delay=delay).invoke.defer()

    def __load_checkpoint(self):
        records = self.monitor.get("checkpoint", limit=1)
        return MonitorWatcherCheckpoint.deserialize(records[0][1]) if records else None

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
        cursors (Mapping[String, Integer]) - the cursors (update versions) by agent name
        core_version (Optional[Integer]) - the version of the snapshot core
            Could be $None if there were no saved snapshots.
        payload_versions (Mapping[String, Integer]) - the payload versions by task alias
    """

    cursors = MappingField(StringField, IntegerField)
    core_version = OptionalField(IntegerField)
    payload_versions = MappingField(StringField, IntegerField)

    def __init__(self, cursors, core_version, payload_versions):
        """
        Args:
            cursors (Mapping[String, Integer])
            core_version (Optional[Integer])
            payload_versions (Mapping[String, Integer])
        """
        self.cursors = cursors
        self.core_version = core_version
        self.payload_versions = payload_versions
