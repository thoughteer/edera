from edera.routine import deferrable
from edera.routine import routine
from edera.workflow.executor import WorkflowExecutor


class MonitoringWorkflowExecutor(WorkflowExecutor):
    """
    A workflow executor that monitors the state of the workflow via an agent.

    See also:
        $MonitoringAgent
    """

    def __init__(self, base, agent):
        """
        Args:
            base (WorkflowExecutor) - a base workflow executor
            agent (MonitoringAgent) - a monitoring agent
        """
        self.__base = base
        self.__agent = agent

    @routine
    def execute(self, workflow):
        yield deferrable(self.__base.execute).defer(self.__agent.embrace(workflow))
