import time

import pytest

from edera.exceptions import ExcusableError
from edera.workers import ProcessWorker
from edera.workers import ThreadWorker


@pytest.fixture(params=[ProcessWorker, ThreadWorker])
def worker(request):
    return request.param("worker", lambda: time.sleep(1.0))


@pytest.fixture(params=[ProcessWorker, ThreadWorker])
def terminated_worker(request):

    def terminate():
        raise SystemExit("why?")

    return request.param("worker", terminate)


@pytest.fixture(params=[ProcessWorker, ThreadWorker])
def stopping_worker(request):

    def stop():
        raise ExcusableError("okay")

    return request.param("worker", stop)


@pytest.fixture(params=[ProcessWorker, ThreadWorker])
def failing_worker(request):

    def fail():
        raise RuntimeError("not okay")

    return request.param("worker", fail)


@pytest.fixture(params=[ProcessWorker, ThreadWorker])
def hanging_worker(request):

    def hang():
        while True:
            time.sleep(1.0)

    return request.param("worker", hang)
