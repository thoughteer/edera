import datetime


def test_worker_works_correctly(worker):
    assert not worker.alive
    assert not worker.failed
    assert not worker.stopped
    worker.start()
    assert worker.alive
    assert not worker.failed
    assert not worker.stopped
    worker.join(datetime.timedelta(seconds=3.0))
    assert not worker.alive
    assert not worker.failed
    assert not worker.stopped


def test_worker_terminates_silently(terminated_worker):
    terminated_worker.start()
    terminated_worker.join(datetime.timedelta(seconds=3.0))
    assert not terminated_worker.alive
    assert not terminated_worker.failed
    assert not terminated_worker.stopped


def test_worker_stops_gracefully(stopping_worker):
    stopping_worker.start()
    stopping_worker.join(datetime.timedelta(seconds=3.0))
    assert not stopping_worker.alive
    assert not stopping_worker.failed
    assert stopping_worker.stopped


def test_worker_fails_gracefully(failing_worker):
    failing_worker.start()
    failing_worker.join(datetime.timedelta(seconds=3.0))
    assert not failing_worker.alive
    assert failing_worker.failed
    assert not failing_worker.stopped


def test_worker_can_be_killed(hanging_worker):
    hanging_worker.start()
    hanging_worker.join(datetime.timedelta(seconds=3.0))
    assert hanging_worker.alive
    hanging_worker.kill()
    assert not hanging_worker.alive
    assert not hanging_worker.failed
    assert not hanging_worker.stopped
