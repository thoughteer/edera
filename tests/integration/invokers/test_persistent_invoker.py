import datetime
import threading
import time

import pytest

from edera import routine
from edera.exceptions import ExcusableError
from edera.invokers import PersistentInvoker


def test_invoker_runs_action_with_given_delay():

    @routine
    def append_current_timestamp():
        counter[0] += 1
        yield
        timestamps.append(datetime.datetime.utcnow())

    def audit():
        if counter[0] > limit:
            raise RuntimeError

    timestamps = []
    counter = [0]
    limit = 3
    delay = datetime.timedelta(seconds=1.0)
    with pytest.raises(RuntimeError):
        PersistentInvoker(append_current_timestamp, delay=delay).invoke[audit]()
    assert len(timestamps) == limit
    assert abs((timestamps[2] - timestamps[0]) - (limit - 1) * delay) < delay


def test_invoker_runs_action_forever():

    def append_current_timestamp():
        counter[0] += 1
        raise ExcusableError("to be swallowed")

    def audit():
        if interrupted:
            raise RuntimeError

    counter = [0]
    interrupted = False
    delay = datetime.timedelta(seconds=0.1)
    invoker = PersistentInvoker(append_current_timestamp, delay=delay)
    invoker_thread = threading.Thread(target=invoker.invoke[audit])
    invoker_thread.daemon = True
    invoker_thread.start()
    time.sleep(0.3)
    assert invoker_thread.is_alive()
    assert counter[0] >= 1
    time.sleep(0.3)
    assert invoker_thread.is_alive()
    assert counter[0] >= 3
    interrupted = True
    time.sleep(0.3)
    assert not invoker_thread.is_alive()
    invoker_thread.join()
