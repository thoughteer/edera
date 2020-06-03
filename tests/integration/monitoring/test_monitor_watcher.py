import datetime

import pytest

import edera.helpers

from edera import routine
from edera import Timer
from edera.exceptions import MonitorInconsistencyError
from edera.invokers import MultiThreadedInvoker
from edera.monitoring import MonitoringAgent
from edera.monitoring.snapshot import TaskLogUpdate


def test_monitor_watcher_works_correctly_even_after_restart(monitor, consumer, watcher):

    @routine
    def watch():
        yield watcher.run.defer(delay=datetime.timedelta(milliseconds=10))

    core = watcher.load_snapshot_core()
    assert core.states[core.aliases["O"]].completed
    assert core.states[core.aliases["X"]].completed
    assert not core.states[core.aliases["Y"]].completed
    payload = watcher.load_task_payload(core.aliases["X"])
    assert payload.dependencies == {core.aliases["O"]}
    newbie = MonitoringAgent("newbie", monitor, consumer)
    newbie.register()
    newbie.push(TaskLogUpdate("O", "oops", edera.helpers.now()))
    timer = Timer(datetime.timedelta(milliseconds=100))
    try:
        MultiThreadedInvoker({"w": watch}).invoke[timer]()
    except Timer.Timeout:
        pass


def test_monitor_watcher_ignores_agent_errors(broken_watcher):

    @routine
    def watch():
        yield broken_watcher.run.defer(delay=datetime.timedelta(milliseconds=10))

    timer = Timer(datetime.timedelta(milliseconds=200))
    try:
        MultiThreadedInvoker({"w": watch}).invoke[timer]()
    except Timer.Timeout:
        pass


def test_monitor_watcher_detects_inconsistent_snapshot_core(monitor, watcher):

    @routine
    def watch():
        with pytest.raises(MonitorInconsistencyError):
            yield watcher.run.defer(delay=datetime.timedelta(milliseconds=10))

    monitor.delete("core")
    timer = Timer(datetime.timedelta(milliseconds=200))
    try:
        MultiThreadedInvoker({"w": watch}).invoke[timer]()
    except Timer.Timeout:
        pass


def test_monitor_watcher_detects_inconsistent_task_payloads(monitor, watcher):

    @routine
    def watch():
        with pytest.raises(MonitorInconsistencyError):
            yield watcher.run.defer(delay=datetime.timedelta(milliseconds=10))

    monitor.delete("payload/08a914cde0")
    timer = Timer(datetime.timedelta(milliseconds=200))
    try:
        MultiThreadedInvoker({"w": watch}).invoke[timer]()
    except Timer.Timeout:
        pass
