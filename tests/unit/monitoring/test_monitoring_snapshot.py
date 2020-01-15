import collections

import edera.helpers

from edera.monitoring import MonitoringSnapshot
from edera.monitoring.snapshot import MonitoringSnapshotCore
from edera.monitoring.snapshot import TaskLogUpdate
from edera.monitoring.snapshot import TaskPayload
from edera.monitoring.snapshot import TaskState
from edera.monitoring.snapshot import TaskStatusUpdate
from edera.monitoring.snapshot import WorkflowUpdate


def test_task_state_has_correct_structure():
    state = TaskState("T")
    assert state.name == "T"
    assert not state.phony
    assert not state.completed
    assert not state.stale
    assert isinstance(state.agents, collections.Set)
    assert not state.agents
    assert isinstance(state.runs, collections.Mapping)
    assert not state.runs
    assert isinstance(state.failures, collections.Mapping)
    assert not state.failures
    assert state.span is None
    assert isinstance(state.baggage, collections.Mapping)
    assert not state.baggage


def test_task_state_is_serializable():
    state = TaskState("T")
    assert TaskState.deserialize(state.serialize()).name == "T"


def test_tasks_can_be_added_to_snapshot_core():
    core = MonitoringSnapshotCore({}, {})
    core.add(["A", "B"])
    assert set(core.aliases) == {"A", "B"}
    for name in ["A", "B"]:
        alias = core.aliases[name]
        assert isinstance(core.states[alias], TaskState)
        assert core.states[alias].name == name


def test_snapshot_core_is_serializable():
    core = MonitoringSnapshotCore({}, {})
    core.add(["A", "B"])
    assert set(MonitoringSnapshotCore.deserialize(core.serialize()).aliases) == {"A", "B"}


def test_task_payload_has_correct_structure():
    payload = TaskPayload()
    assert payload.dependencies is None
    assert isinstance(payload.logs, collections.Mapping)
    assert not payload.logs


def test_empty_task_payload_is_serializable():
    payload = TaskPayload()
    assert TaskPayload.deserialize(payload.serialize()).dependencies is None
    assert TaskPayload.deserialize(payload.serialize()).dependencies is None


def test_nonempty_task_payload_is_serializable():
    payload = TaskPayload()
    payload.dependencies = {"A", "B"}
    assert TaskPayload.deserialize(payload.serialize()).dependencies == {"A", "B"}


def test_tasks_can_be_added_to_snapshot():
    snapshot = MonitoringSnapshot.void()
    snapshot.add(["A", "B"])
    assert set(snapshot.core.aliases) == {"A", "B"}
    for name in ["A", "B"]:
        assert name in snapshot
        alias = snapshot.core.aliases[name]
        assert isinstance(snapshot.core.states[alias], TaskState)
        assert snapshot.core.states[alias].name == name
        assert isinstance(snapshot.payloads[alias], TaskPayload)


def test_workflow_update_adds_only_missing_tasks():
    snapshot = MonitoringSnapshot.void()
    snapshot.add(["A"])
    alias = snapshot.core.aliases["A"]
    state = snapshot.core.states[alias]
    dependencies = {"A": {"B"}, "B": set()}
    update = WorkflowUpdate(dependencies, set(), {})
    list(update.apply(snapshot, "agent"))
    assert "B" in snapshot
    assert snapshot.core.states[alias] is state


def test_workflow_update_marks_agent_as_not_running_any_task():
    snapshot = MonitoringSnapshot.void()
    snapshot.add(["A", "B"])
    snapshot.core.states[snapshot.core.aliases["A"]].runs = {"agent": edera.helpers.now()}
    snapshot.core.states[snapshot.core.aliases["B"]].runs = {"agent": edera.helpers.now()}
    dependencies = {"A": set()}
    update = WorkflowUpdate(dependencies, set(), {})
    list(update.apply(snapshot, "agent"))
    assert not snapshot.core.states[snapshot.core.aliases["A"]].runs
    assert not snapshot.core.states[snapshot.core.aliases["B"]].runs


def test_workflow_update_marks_phony_tasks():
    snapshot = MonitoringSnapshot.void()
    dependencies = {"A": {"B"}, "B": set()}
    update = WorkflowUpdate(dependencies, {"A"}, {})
    list(update.apply(snapshot, "agent"))
    assert snapshot.core.states[snapshot.core.aliases["A"]].phony
    assert not snapshot.core.states[snapshot.core.aliases["B"]].phony


def test_workflow_update_registers_active_agents():
    snapshot = MonitoringSnapshot.void()
    dependencies = {"A": set()}
    update = WorkflowUpdate(dependencies, set(), {})
    list(update.apply(snapshot, "agent-1"))
    list(update.apply(snapshot, "agent-2"))
    assert snapshot.core.states[snapshot.core.aliases["A"]].agents == {"agent-1", "agent-2"}


def test_workflow_update_registers_active_agents():
    snapshot = MonitoringSnapshot.void()
    dependencies = {"A": set()}
    update = WorkflowUpdate(dependencies, set(), {})
    list(update.apply(snapshot, "agent-1"))
    list(update.apply(snapshot, "agent-2"))
    assert snapshot.core.states[snapshot.core.aliases["A"]].agents == {"agent-1", "agent-2"}


def test_workflow_update_marks_tasks_as_nonstale():
    snapshot = MonitoringSnapshot.void()
    snapshot.add(["A"])
    snapshot.core.states[snapshot.core.aliases["A"]].stale = True
    dependencies = {"A": set()}
    update = WorkflowUpdate(dependencies, set(), {})
    list(update.apply(snapshot, "agent"))
    assert not snapshot.core.states[snapshot.core.aliases["A"]].stale


def test_workflow_update_saves_baggages():
    snapshot = MonitoringSnapshot.void()
    baggage = {"key": "value"}
    dependencies = {"A": set()}
    update = WorkflowUpdate(dependencies, {}, {"A": baggage})
    list(update.apply(snapshot, "agent"))
    assert snapshot.core.states[snapshot.core.aliases["A"]].baggage == baggage


def test_workflow_update_adds_missing_dependencies():
    snapshot = MonitoringSnapshot.void()
    dependencies = {"X": {"A", "B"}, "A": set(), "B": set()}
    update = WorkflowUpdate(dependencies, set(), {})
    assert set(update.apply(snapshot, "agent")) == {"A", "B", "X"}
    assert snapshot.payloads[snapshot.core.aliases["A"]].dependencies is not None
    assert snapshot.payloads[snapshot.core.aliases["B"]].dependencies is not None
    assert len(snapshot.payloads[snapshot.core.aliases["X"]].dependencies) == 2
    dependencies = {"Y": {"X"}, "X": {"A", "B"}, "A": set(), "B": set()}
    update = WorkflowUpdate(dependencies, set(), {})
    assert set(update.apply(snapshot, "agent")) == {"Y"}
    assert len(snapshot.payloads[snapshot.core.aliases["Y"]].dependencies) == 1


def test_workflow_update_detects_stale_tasks_correctly():
    snapshot = MonitoringSnapshot.void()
    list(WorkflowUpdate({"C1": {"B1"}, "B1": {"A"}, "A": set()}, set(), {}).apply(snapshot, "X"))
    list(WorkflowUpdate({"C1": {"B1"}, "B1": set()}, set(), {}).apply(snapshot, "X"))
    assert snapshot.core.states[snapshot.core.aliases["A"]].completed
    assert not snapshot.core.states[snapshot.core.aliases["A"]].stale
    list(WorkflowUpdate({"C2": {"B2"}, "B2": {"A"}, "A": set()}, set(), {}).apply(snapshot, "X"))
    assert snapshot.core.states[snapshot.core.aliases["A"]].completed
    assert not snapshot.core.states[snapshot.core.aliases["A"]].stale
    assert snapshot.core.states[snapshot.core.aliases["B1"]].stale
    assert snapshot.core.states[snapshot.core.aliases["C1"]].stale
    list(WorkflowUpdate({"C1": {"B1"}, "B1": set()}, set(), {}).apply(snapshot, "Y"))
    assert not snapshot.core.states[snapshot.core.aliases["B1"]].stale
    assert not snapshot.core.states[snapshot.core.aliases["C1"]].stale


def test_task_status_update_adds_missing_task():
    snapshot = MonitoringSnapshot.void()
    timestamp = edera.helpers.now()
    list(TaskStatusUpdate("T", "running", timestamp).apply(snapshot, "agent"))
    assert "T" in snapshot


def test_task_status_update_handles_no_run_completion_right():
    snapshot = MonitoringSnapshot.void()
    timestamp = edera.helpers.now()
    list(TaskStatusUpdate("T", "completed", timestamp).apply(snapshot, "agent"))
    assert snapshot.core.states[snapshot.core.aliases["T"]].completed
    assert snapshot.core.states[snapshot.core.aliases["T"]].span is None


def test_task_status_update_handles_normal_completion_right():
    snapshot = MonitoringSnapshot.void()
    timestamp = edera.helpers.now()
    list(TaskStatusUpdate("T", "running", timestamp).apply(snapshot, "agent"))
    assert "agent" in snapshot.core.states[snapshot.core.aliases["T"]].runs
    list(TaskStatusUpdate("T", "completed", timestamp).apply(snapshot, "agent"))
    assert not snapshot.core.states[snapshot.core.aliases["T"]].runs
    assert snapshot.core.states[snapshot.core.aliases["T"]].completed
    assert snapshot.core.states[snapshot.core.aliases["T"]].span == (timestamp, timestamp)


def test_task_status_update_handles_failures_right():
    snapshot = MonitoringSnapshot.void()
    timestamp = edera.helpers.now()
    list(TaskStatusUpdate("T", "running", timestamp).apply(snapshot, "agent"))
    list(TaskStatusUpdate("T", "failed", timestamp).apply(snapshot, "agent"))
    assert "agent" in snapshot.core.states[snapshot.core.aliases["T"]].failures
    assert not snapshot.core.states[snapshot.core.aliases["T"]].runs
    assert not snapshot.core.states[snapshot.core.aliases["T"]].completed
    assert snapshot.core.states[snapshot.core.aliases["T"]].span is None


def test_task_log_update_adds_missing_task():
    snapshot = MonitoringSnapshot.void()
    timestamp = edera.helpers.now()
    list(TaskLogUpdate("T", "message", timestamp).apply(snapshot, "agent"))
    assert "T" in snapshot


def test_task_log_update_prepends_messages():
    snapshot = MonitoringSnapshot.void()
    timestamp = edera.helpers.now()
    assert list(TaskLogUpdate("T", "hello", timestamp).apply(snapshot, "agent")) == ["T"]
    assert snapshot.payloads[snapshot.core.aliases["T"]].logs == {
        "agent": [(timestamp, "hello")],
    }
    assert list(TaskLogUpdate("T", "world", timestamp).apply(snapshot, "agent")) == ["T"]
    assert snapshot.payloads[snapshot.core.aliases["T"]].logs == {
        "agent": [(timestamp, "world"), (timestamp, "hello")],
    }


def test_task_log_update_keeps_limited_number_of_messages():
    snapshot = MonitoringSnapshot.void()
    timestamp = edera.helpers.now()
    limit = TaskLogUpdate.LIMIT
    for i in range(limit + 1):
        list(TaskLogUpdate("T", str(i), timestamp).apply(snapshot, "agent"))
    assert len(snapshot.payloads[snapshot.core.aliases["T"]].logs["agent"]) == limit
    assert snapshot.payloads[snapshot.core.aliases["T"]].logs["agent"][0][1] == str(limit)
