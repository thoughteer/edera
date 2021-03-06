import datetime
import logging
import os
import os.path

import edera.helpers

from edera.condition import Condition
from edera.daemon import Daemon
from edera.daemon import DaemonAutoTester
from edera.daemon import DaemonModule
from edera.daemon import DaemonSchedule
from edera.daemon import StaticDaemonModule
from edera.parameterizable import Parameter
from edera.parameterizable import Parameterizable
from edera.qualifiers import DiscreteDateTime
from edera.requisites import Annotate
from edera.requisites import shortcut
from edera.routine import routine
from edera.task import Task
from edera.testing import DefaultScenario
from edera.testing import ScenarioWithProvidedStubs
from edera.testing import TestableTask

from .beans import arguments
from .beans import cache
from .beans import colorbox
from .beans import fs
from .beans import locker
from .beans import monitor


SINK = logging.getLogger("edera.monitoring.sink")


class PathExists(Parameterizable, Condition):

    path = Parameter()

    def check(self):
        return fs.check(self.path)

    @property
    def invariants(self):
        if self.path:
            yield self >> PathExists(path=os.path.dirname(self.path))


class CreateDirectory(Parameterizable, TestableTask):

    path = Parameter()

    @routine
    def execute(self):
        yield edera.helpers.sleep.defer(datetime.timedelta(seconds=arguments.sleep))
        fs.ensure(self.path)

    @shortcut
    def requisite(self):
        if self.path:
            return CreateDirectory(path=os.path.dirname(self.path))

    @property
    def target(self):
        return PathExists(path=self.path)


class DownloadFile(Parameterizable, TestableTask):

    path = Parameter()

    @routine
    def execute(self):
        yield edera.helpers.sleep.defer(datetime.timedelta(seconds=arguments.sleep))
        with fs.create(self.path) as stream:
            stream.write("real\ndata\n")  # imagine we actually download some stuff here

    @shortcut
    def requisite(self):
        yield CreateDirectory(path=os.path.dirname(self.path))

    @property
    def target(self):
        return PathExists(path=self.path)

    @property
    def tests(self):
        yield self.Validate()

    class Validate(DefaultScenario):

        @routine
        def run(self, subject):
            yield DefaultScenario.run.defer(self, subject)
            with fs.read(subject.unwrap().path) as stream:
                result = stream.read()
            assert result == "real\ndata\n"

    class Mock(Parameterizable, DefaultScenario):

        data = Parameter()

        def run(self, subject):
            with fs.create(subject.unwrap().path) as stream:
                stream.write(self.data)


class HashEachLine(Parameterizable, Task):

    input_file = Parameter()
    output_file = Parameter()
    salt = Parameter()

    @routine
    def execute(self):
        SINK.info("Learn more: https://duckduckgo.com/?q=sha-1")
        yield edera.helpers.sleep.defer(datetime.timedelta(seconds=arguments.sleep))
        with fs.read(self.input_file) as input_stream:
            with fs.create(self.output_file) as output_stream:
                for line in input_stream:
                    output_stream.write(edera.helpers.sha1(self.salt + line.rstrip("\n")) + "\n")
                    yield

    @shortcut
    def requisite(self):
        return CreateDirectory(path=os.path.dirname(self.output_file))

    @property
    def target(self):
        return PathExists(path=self.output_file)

    class Validate(ScenarioWithProvidedStubs, DefaultScenario):

        input_data = "fake\ndata\n"

        @routine
        def run(self, subject):
            yield DefaultScenario.run.defer(self, subject)
            with fs.read(subject.unwrap().output_file) as stream:
                result = [line.rstrip() for line in stream]
            assert len(result) == 2
            assert all(len(line) == 40 for line in result)

        def stub(self, subject, dependencies):
            result = DefaultScenario.stub(self, subject, dependencies)
            result.update(self.stubs)
            return result

    class Mock(Parameterizable, DefaultScenario):

        data = Parameter()

        def run(self, subject):
            with fs.create(subject.unwrap().output_file) as stream:
                stream.write(self.data)

        def stub(self, subject, dependencies):
            return {
                dependency: DefaultScenario()
                for dependency in dependencies
                if isinstance(dependency.unwrap(), CreateDirectory)
            }


class PickFirstLetters(Parameterizable, Task):

    input_file = Parameter()
    output_file = Parameter()

    @routine
    def execute(self):
        yield edera.helpers.sleep.defer(datetime.timedelta(seconds=arguments.sleep))
        with fs.read(self.input_file) as input_stream:
            with fs.create(self.output_file) as output_stream:
                for line in input_stream:
                    output_stream.write(line[0])
                    yield

    @shortcut
    def requisite(self):
        yield Annotate("tag", "focus")
        yield CreateDirectory(path=os.path.dirname(self.output_file))

    @property
    def target(self):
        return PathExists(path=self.output_file)

    class Validate(ScenarioWithProvidedStubs, DefaultScenario):

        input_data = "abc\ndef\n"

        @routine
        def run(self, subject):
            yield DefaultScenario.run.defer(self, subject)
            with fs.read(subject.unwrap().output_file) as stream:
                result = stream.read()
            assert result == "ad"

        def stub(self, subject, dependencies):
            result = DefaultScenario.stub(self, subject, dependencies)
            result.update(self.stubs)
            return result

    class Mock(Parameterizable, DefaultScenario):

        data = Parameter()

        def run(self, subject):
            with fs.create(subject.unwrap().output_file) as stream:
                stream.write(self.data)

        def stub(self, subject, dependencies):
            return {
                dependency: DefaultScenario()
                for dependency in dependencies
                if isinstance(dependency.unwrap(), CreateDirectory)
            }


class RemoveFile(Parameterizable, Task):

    path = Parameter()

    @routine
    def execute(self):
        if self.target.check():
            return
        yield edera.helpers.sleep.defer(datetime.timedelta(seconds=arguments.sleep))
        fs.remove(self.path)

    @property
    def target(self):
        return ~PathExists(path=self.path)

    class Validate(ScenarioWithProvidedStubs, DefaultScenario):
        pass


class HashFile(Parameterizable, TestableTask):

    input_file = Parameter()
    output_file = Parameter()
    salt = Parameter()

    @property
    def buffer_file(self):
        return self.output_file + ".buffer"

    @property
    def buffer_remover(self):
        return RemoveFile(path=self.buffer_file)

    @property
    def input_downloader(self):
        return DownloadFile(path=self.input_file)

    @property
    def letter_picker(self):
        return PickFirstLetters(input_file=self.buffer_file, output_file=self.output_file)

    @property
    def line_hasher(self):
        return HashEachLine(
            input_file=self.input_file, output_file=self.buffer_file, salt=self.salt)

    @shortcut
    def requisite(self):
        yield {
            self.line_hasher: self.input_downloader,
            self.letter_picker: self.line_hasher,
            self.buffer_remover: [self.letter_picker, self.line_hasher],
            self: self.letter_picker,
        }
        yield {
            self.line_hasher: Annotate(
                "tests",
                [
                    self.line_hasher.Validate(
                        stubs={
                            self.input_downloader: self.input_downloader.Mock(data=self.line_hasher.Validate.input_data),
                        }),
                ]),
            self.letter_picker: Annotate(
                "tests",
                [
                    self.letter_picker.Validate(
                        stubs={
                            self.line_hasher: self.line_hasher.Mock(data=self.letter_picker.Validate.input_data),
                        }),
                ]),
            self.buffer_remover: Annotate(
                "tests",
                [
                    self.buffer_remover.Validate(
                        stubs={
                            self.line_hasher: self.line_hasher.Mock(data=""),
                        }),
                ]),
        }


class DivideByZero(Task):

    @routine
    def execute(self):
        yield edera.helpers.sleep.defer(datetime.timedelta(seconds=arguments.sleep))
        1 / 0


class ReHashFile(Parameterizable, Task):

    input_file = Parameter()
    output_directory = Parameter()
    timestamp = Parameter(DiscreteDateTime("PT1M"))

    @shortcut
    def requisite(self):
        if arguments.fail:
            yield DivideByZero()
        for shift in range(5):
            timestamp = self.timestamp - datetime.timedelta(minutes=shift)
            salt = timestamp.strftime("%Y-%m-%dT%H:%M")
            output_file = os.path.join(self.output_directory, salt)
            yield HashFile(input_file=self.input_file, output_file=output_file, salt=salt)


class DemoMain(DaemonModule):

    @property
    def scheduling(self):
        return {
            None: DaemonSchedule(executor_count=2, execution_delay="PT3S"),
            "focus": DaemonSchedule(executor_count=5, execution_delay="PT1S"),
        }

    def seed(self, now):
        return ReHashFile(input_file="input", output_directory="output", timestamp=now)


class Welcome(Parameterizable, Task):

    @routine
    def execute(self):
        yield edera.helpers.sleep.defer(datetime.timedelta(seconds=arguments.sleep))
        SINK.info("Welcome!")


class DemoPrelude(StaticDaemonModule):

    root = Welcome()
    scheduling = {None: DaemonSchedule(execution_delay="PT1S")}


class DemoDaemonAutoTester(DaemonAutoTester):

    box = colorbox
    registry = cache

    def finish(self):
        with fs.create("TESTED"):
            pass


class DemoDaemon(Daemon):

    autotester = DemoDaemonAutoTester() if arguments.test else None
    locker = locker
    cache = cache
    monitor = monitor
    prelude = DemoPrelude()
    main = DemoMain()


if __name__ == "__main__":
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(processName)s/%(threadName)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.WARN)
    logging.getLogger("edera").setLevel(logging.DEBUG if arguments.debug else logging.INFO)
    DemoDaemon().run()
