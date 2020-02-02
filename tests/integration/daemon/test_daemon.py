import datetime
import multiprocessing
import os
import os.path
import time

import iso8601
import pytest

from edera import Condition
from edera import Parameter
from edera import Parameterizable
from edera import Task
from edera import Timer
from edera.daemon import Daemon
from edera.daemon import DaemonAutoTester
from edera.daemon import DaemonModule
from edera.daemon import DaemonSchedule
from edera.daemon import StaticDaemonModule
from edera.helpers import SimpleBox
from edera.lockers import DirectoryLocker
from edera.monitoring import MonitorWatcher
from edera.storages import SQLiteStorage
from edera.testing import TestableTask


class FileSystem(object):

    def __init__(self, root):
        self.root = root

    def check(self, path):
        return os.path.exists(os.path.join(self.root, path))

    def create(self, path):
        if not os.path.exists(self.root):
            os.makedirs(self.root)
        with open(os.path.join(self.root, path), "w"):
            pass


def test_daemon_can_idle():

    class Idle(Task):
        pass

    class MainModule(StaticDaemonModule):

        root = Idle()

    class MyDaemon(Daemon):

        main = MainModule()

    daemon = MyDaemon()
    with pytest.raises(Timer.Timeout):
        daemon.run[Timer(datetime.timedelta(seconds=5))]()


def test_daemon_functions_correctly_in_production_mode(tmpdir):

    class FileExists(Parameterizable, Condition):

        path = Parameter()

        def check(self):
            return fs.check(self.path)

    class CreateFile(Parameterizable, Task):

        path = Parameter()

        def execute(self):
            fs.create(self.path)

        @property
        def target(self):
            return FileExists(path=self.path)

    class SupportModule(StaticDaemonModule):

        root = CreateFile(path="support")

    class PreludeModule(StaticDaemonModule):

        root = CreateFile(path="prelude")

    class MainModule(DaemonModule):

        scheduling = {
            None: DaemonSchedule(building_delay="PT1S", execution_delay="PT1S", executor_count=2),
        }

        def seed(self, now):
            path = "main." + now.astimezone(iso8601.UTC).strftime("%Y-%m-%dT%H:%M:%S")
            return CreateFile(path=path)

    class MyDaemon(Daemon):

        cache = SQLiteStorage(str(tmpdir.join("cache.db")))
        locker = DirectoryLocker(str(tmpdir.join("locks")))
        monitor = SQLiteStorage(str(tmpdir.join("monitor.db")))

        support = SupportModule()
        prelude = PreludeModule()
        main = MainModule()

    fs = FileSystem(str(tmpdir))
    daemon = MyDaemon()
    process = multiprocessing.Process(target=daemon.run)
    process.start()
    time.sleep(15)
    process.terminate()
    process.join(15)
    files = set(path.basename for path in tmpdir.listdir())
    assert "cache.db" in files
    assert "locks" in files
    assert "monitor.db" in files
    assert "support" in files
    assert "prelude" in files
    assert 3 <= len([name for name in files if name.startswith("main.")]) <= 11
    watcher = MonitorWatcher(MyDaemon.monitor)
    assert len(watcher.load_snapshot_core().states) >= 5


def test_daemon_functions_correctly_in_autotesting_mode(tmpdir):

    class FileExists(Parameterizable, Condition):

        path = Parameter()

        def check(self):
            return fs().check(self.path)

    class CreateFile(Parameterizable, TestableTask):

        path = Parameter()

        def execute(self):
            fs().create(self.path)

        @property
        def target(self):
            return FileExists(path=self.path)

    class PreludeModule(StaticDaemonModule):

        root = CreateFile(path="prelude")

    class MainModule(DaemonModule):

        scheduling = {
            None: DaemonSchedule(building_delay="PT1S", execution_delay="PT1S", executor_count=2),
        }

        def seed(self, now):
            path = "main." + now.astimezone(iso8601.UTC).strftime("%Y-%m-%dT%H:%M:%S")
            return CreateFile(path=path)

    class MyDaemon(Daemon):

        cache = SQLiteStorage(str(tmpdir.join("cache.db")))
        locker = DirectoryLocker(str(tmpdir.join("locks")))
        monitor = SQLiteStorage(str(tmpdir.join("monitor.db")))

        colorbox = SimpleBox()
        autotester = DaemonAutoTester(colorbox, cache)

        prelude = PreludeModule()
        main = MainModule()

    def fs():
        color = MyDaemon.colorbox.get()
        root = str(tmpdir) if color is None else str(tmpdir.join(color))
        return FileSystem(root)

    daemon = MyDaemon()
    process = multiprocessing.Process(target=daemon.run)
    process.start()
    time.sleep(10)
    process.terminate()
    process.join(10)
    files = set(path.basename for path in tmpdir.listdir())
    assert "cache.db" in files
    assert "locks" in files
    assert "monitor.db" in files
    assert "prelude" in files
    assert "4707242e" in files
    assert tmpdir.join("4707242e").listdir()[0].basename == "main.1991-07-26T09:00:00"
    watcher = MonitorWatcher(MyDaemon.monitor)
    assert len(watcher.load_snapshot_core().states) == 2
