import logging

import pytest

from edera.condition import Condition
from edera.exceptions import ConsumptionError
from edera.exceptions import ExcusableError
from edera.monitoring import MonitoringAgent
from edera.monitoring.agent import LogCapturingTaskWrapper
from edera.monitoring.agent import StatusReportingTaskWrapper
from edera.monitoring.snapshot import WorkflowUpdate
from edera.requisites import Annotate
from edera.requisites import shortcut
from edera.task import Task
from edera.workflow import WorkflowBuilder


def test_agent_can_register_and_be_discovered(monitor, agent):
    assert not agent.passive
    assert not MonitoringAgent.discover(monitor)
    agent.register()
    assert MonitoringAgent.discover(monitor) == {agent}
    agent.register()
    assert MonitoringAgent.discover(monitor) == {agent}


def test_agent_can_push_and_pull_updates(agent):
    update = WorkflowUpdate({}, set(), {})
    agent.push(update)
    updates = agent.pull()
    assert len(updates) == 1
    assert isinstance(updates[0][1], WorkflowUpdate)
    cursor = updates[0][0]
    agent.push(update)
    assert len(agent.pull()) == 2
    updates = agent.pull(since=(cursor + 1))
    assert len(updates) == 1


def test_agent_can_drop_updates(agent):
    update = WorkflowUpdate({}, set(), {})
    agent.push(update)
    agent.push(update)
    updates = agent.pull()
    assert len(updates) == 2
    cursor = updates[0][0]
    agent.drop(till=cursor)
    assert len(agent.pull()) == 1
    agent.drop()
    assert not agent.pull()


def test_agent_embraces_workflow_correctly(agent):

    class A(Task):

        def execute(self):
            pass

    class B(Task):

        @shortcut
        def requisite(self):
            yield A()
            yield Annotate("baggage", {"key": "value"})

    workflow = WorkflowBuilder().build(B())
    result = agent.embrace(workflow)
    updates = agent.pull()
    assert len(updates) == 1
    assert updates[0][1].dependencies == {"A": set(), "B": {"A"}}
    assert updates[0][1].phonies == {"B"}
    assert updates[0][1].baggages == {"B": {"key": "value"}}
    a = result[A()].item
    assert isinstance(a, LogCapturingTaskWrapper)
    assert isinstance(a.unwrap(), StatusReportingTaskWrapper)
    assert isinstance(a.unwrap().unwrap(), A)
    assert isinstance(result[B()].item, B)


def test_agent_ignores_consumption_errors(mocker, consumer, agent):
    consumer.consume = mocker.Mock(side_effect=ConsumptionError)
    agent.push(WorkflowUpdate({}, set(), {}))
    assert not agent.pull()


def test_status_reporting_task_wrapper_works_correctly_with_no_target(agent):

    class T(Task):

        def execute(self):
            pass

    wrapper = StatusReportingTaskWrapper(T(), agent)
    assert wrapper.target is None
    wrapper.execute()
    updates = agent.pull()
    assert len(updates) == 2
    assert updates[0][1].status == "completed"
    assert updates[1][1].status == "running"


def test_status_reporting_task_wrapper_works_correctly_with_target(agent):

    class T(Task):

        class Target(Condition):

            def check(self):
                return True

        def execute(self):
            pass

        @property
        def target(self):
            return self.Target()

    wrapper = StatusReportingTaskWrapper(T(), agent)
    wrapper.target.check()
    updates = agent.pull()
    assert len(updates) == 1
    assert updates[0][1].status == "completed"


def test_status_reporting_task_wrapper_reports_stops(agent):

    class T(Task):

        class Target(Condition):

            def check(self):
                raise ExcusableError

        def execute(self):
            raise ExcusableError

        @property
        def target(self):
            return self.Target()

    wrapper = StatusReportingTaskWrapper(T(), agent)
    with pytest.raises(ExcusableError):
        wrapper.target.check()
    assert not agent.pull()
    with pytest.raises(ExcusableError):
        wrapper.execute()
    updates = agent.pull()
    assert len(updates) == 2
    assert updates[0][1].status == "stopped"
    assert updates[1][1].status == "running"


def test_status_reporting_task_wrapper_reports_failures(agent):

    class T(Task):

        class Target(Condition):

            def check(self):
                raise RuntimeError

        def execute(self):
            raise RuntimeError

        @property
        def target(self):
            return self.Target()

    wrapper = StatusReportingTaskWrapper(T(), agent)
    with pytest.raises(RuntimeError):
        wrapper.target.check()
    with pytest.raises(RuntimeError):
        wrapper.execute()
    updates = agent.pull()
    assert len(updates) == 5
    assert updates[0][1].status == "failed"
    assert updates[1][1].message.startswith("Traceback")
    assert updates[2][1].status == "running"
    assert updates[3][1].status == "failed"
    assert updates[4][1].message.startswith("Traceback")


def test_log_capturing_task_wrapper_captures_messages_from_sink(agent):

    class T(Task):

        def execute(self):
            sink.info("hello")
            sink.info("world")

    sink = logging.getLogger("edera.monitoring.sink")
    sink.setLevel(logging.DEBUG)
    wrapper = LogCapturingTaskWrapper(T(), agent)
    wrapper.execute()
    updates = agent.pull()
    assert len(updates) == 2
    assert updates[0][1].message == "world"
    assert updates[1][1].message == "hello"
