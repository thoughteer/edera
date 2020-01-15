from edera import Graph
from edera.workflow.executors import MonitoringWorkflowExecutor


def test_monitoring_workflow_executor_employs_agent(mocker):
    workflow = Graph()
    monitored_workflow = Graph()
    base = mocker.Mock()
    agent = mocker.Mock()
    agent.embrace.return_value = monitored_workflow
    executor = MonitoringWorkflowExecutor(base, agent)
    executor.execute(workflow)
    agent.embrace.assert_called_once_with(workflow)
    base.execute.assert_called_once_with(monitored_workflow)
