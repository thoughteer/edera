import signal
import subprocess
import sys
import threading
import time

from edera.monitoring import MonitoringSnapshot
from edera.storages import SQLiteStorage


def start_analysis(stream):

    def analyze():
        while True:
            line = stream.readline().decode("ASCII")
            if not line:
                break
            sys.stderr.write(line)
            if "ERROR" in line or "WARNING" in line or line.startswith("Traceback"):
                failure.set()
        failure.set()  # the log stream suddenly stopped

    failure = threading.Event()
    analyzer = threading.Thread(target=analyze)
    analyzer.daemon = True
    analyzer.start()
    return failure


def test_demo_daemon_can_print_help():
    command = ["python", "-m", "edera.demo.daemon", "-h"]
    process = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout, stderr = process.communicate()
    assert process.returncode == 0
    assert not stderr
    assert "usage" in stdout.decode("ASCII")


def test_demo_daemon_fails_if_launched_with_no_arguments():
    command = ["python", "-m", "edera.demo.daemon"]
    process = subprocess.Popen(command)
    process.communicate()
    assert process.returncode > 0


def test_demo_daemon_works_fine_in_testing_mode(tmpdir):
    command = ["python", "-m", "edera.demo.daemon", "-d", "-t", str(tmpdir), "-s", "0"]
    process = subprocess.Popen(command, stderr=subprocess.PIPE)
    failure = start_analysis(process.stderr)
    failure.wait(timeout=45.0)
    try:
        assert not failure.is_set()
    finally:
        process.send_signal(signal.SIGINT)
    time.sleep(25.0)
    assert process.poll() == 0
    process.communicate()
    distribution = {len(list(child.visit())) for child in tmpdir.listdir() if child.check(dir=True)}
    assert distribution == {0, 1, 2, 7, 11}


def test_demo_daemon_works_fine_in_production_mode(debugger, tmpdir):
    command = ["python", "-m", "edera.demo.daemon", "-d", str(tmpdir), "-s", "0"]
    process = subprocess.Popen(command, stderr=subprocess.PIPE)
    failure = start_analysis(process.stderr)
    failure.wait(timeout=45.0)
    try:
        assert not failure.is_set()
    finally:
        process.send_signal(signal.SIGTERM)
    time.sleep(25.0)
    assert process.poll() == 0
    process.communicate()
    assert tmpdir.join("input").check()
    assert tmpdir.join("output").check(dir=True)
    children = list(tmpdir.join("output").listdir())
    assert len(children) >= 5
    assert sum(1 for child in children if len(child.basename) != 16) <= 1
    monitor = SQLiteStorage(str(tmpdir.join("monitor.db")))
    snapshot = MonitoringSnapshot.deserialize(monitor.get("snapshot", limit=1)[0][1])
    assert len(snapshot.aliases) == len(snapshot.reports) >= 23
    assert sum(1 for alias in snapshot.reports if snapshot.reports[alias].state.completed) >= 16
    assert sum(1 for alias in snapshot.reports if snapshot.reports[alias].state.runs) >= 1
    assert sum(1 for alias in snapshot.reports if snapshot.reports[alias].state.phony) >= 6
