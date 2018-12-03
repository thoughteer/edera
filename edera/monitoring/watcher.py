import datetime

import six

import edera.helpers

from edera.exceptions import MonitorInconsistencyError
from edera.graph import Graph
from edera.helpers import Serializable
from edera.invokers import PersistentInvoker
from edera.linearizers import DFSLinearizer
from edera.monitoring.agent import MonitoringAgent
from edera.monitoring.snapshot import MonitoringSnapshot
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

    def load_payload(self, alias):
        """
        Load the last available payload for the task alias.

        Args:
            alias (String)

        Returns:
            Optional[TaskPayload]

        Raises:
            StorageOperationError if something went wrong with the storage
        """
        return self.__load_payload(alias)

    def load_snapshot(self):
        """
        Load the last available snapshot.

        Returns:
            Optional[MonitoringSnapshot]

        Raises:
            StorageOperationError if something went wrong with the storage
        """
        return self.__load_snapshot()

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
        snapshot = self.__load_snapshot(version=checkpoint.snapshot_version)
        for alias, payload_version in six.iteritems(checkpoint.payload_versions):
            yield
            snapshot.reports[alias].payload = self.__load_payload(alias, version=payload_version)
        yield (checkpoint, snapshot)

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
                        affected.add(snapshot.aliases[task])
                    checkpoint.cursors[agent.name] = version + 1
            augment()
            yield
            checkpoint.snapshot_version = self.monitor.put("snapshot", snapshot.serialize())
            for alias in set(affected):
                yield
                payload = snapshot.reports[alias].payload
                new_payload_version = self.monitor.put("payload/" + alias, payload.serialize())
                affected.remove(alias)
                commited.add(alias)
                checkpoint.payload_versions[alias] = new_payload_version
            new_checkpoint_version = self.monitor.put("checkpoint", checkpoint.serialize())
            self.monitor.delete("checkpoint", till=new_checkpoint_version)
            self.monitor.delete("snapshot", till=checkpoint.snapshot_version)
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
            for alias in snapshot.reports:
                graph.add(alias)
            for alias in snapshot.reports:
                for dependency in snapshot.reports[alias].state.dependencies:
                    graph.link(dependency, alias)
            pending = set()
            for alias in DFSLinearizer().linearize(graph):
                state = snapshot.reports[alias].state
                if state.completed:
                    continue
                if not state.phony or state.dependencies.intersection(pending):
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

    def __load_payload(self, alias, version=None):
        arguments = {"limit": 1} if version is None else {"since": version}
        records = self.monitor.get("payload/" + alias, **arguments)
        if version is not None and (not records or records[-1][0] != version):
            raise MonitorInconsistencyError("invalid payload version for %s: %d" % (alias, version))
        return TaskPayload.deserialize(records[-1][1]) if records else None

    def __load_snapshot(self, version=None):
        arguments = {"limit": 1} if version is None else {"since": version}
        records = self.monitor.get("snapshot", **arguments)
        if version is not None and (not records or records[-1][0] != version):
            raise MonitorInconsistencyError("invalid snapshot version: %d" % version)
        return MonitoringSnapshot.deserialize(records[-1][1]) if records else None


class MonitorWatcherCheckpoint(Serializable):
    """
    A checkpoint descriptor that contains information needed for recovery.

    Attributes:
        cursors (Mapping[String, Integer]) - the cursors (update versions) by agent name
        snapshot_version (Optional[Integer]) - the version of the snapshot
            Could be $None if there were no saved snapshots.
        payload_versions (Mapping[String, Integer]) - the payload versions by task alias
    """

    def __init__(self, cursors, snapshot_version, payload_versions):
        """
        Args:
            cursors (Mapping[String, Integer])
            snapshot_version (Optional[Integer])
            payload_versions (Mapping[String, Integer])
        """
        self.cursors = cursors
        self.snapshot_version = snapshot_version
        self.payload_versions = payload_versions
