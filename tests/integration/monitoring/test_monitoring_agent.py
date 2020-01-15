import logging
import threading

from edera.monitoring.agent import LogCapturingTaskWrapper
from edera.task import Task


def test_log_capturing_task_wrapper_ignores_messages_from_other_threads(mocker):

    class T(Task):

        def execute(self):
            pass

    def log():
        sink.info("none")

    def interfere():
        interferer = threading.Thread(target=log)
        interferer.daemon = True
        interferer.start()
        interferer.join()

    sink = logging.getLogger("edera.monitoring.sink")
    sink.setLevel(logging.DEBUG)
    agent = mocker.Mock()
    wrapper = LogCapturingTaskWrapper(T(), agent)
    wrapper.execute[interfere]()
    assert not agent.push.called
