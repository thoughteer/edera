import abc
import datetime
import logging
import multiprocessing
import signal
import socket
import threading

import six

import edera.helpers

from edera.consumers import InterProcessConsumer
from edera.flags import InterProcessFlag
from edera.flags import InterThreadFlag
from edera.helpers import Sasha
from edera.helpers import SimpleBox
from edera.invokers import MultiProcessInvoker
from edera.invokers import MultiThreadedInvoker
from edera.invokers import PersistentInvoker
from edera.managers import CascadeManager
from edera.monitoring import MonitoringAgent
from edera.monitoring import MonitorWatcher
from edera.routine import deferrable
from edera.routine import routine
from edera.workflow.builder import WorkflowBuilder
from edera.workflow.executors import BasicWorkflowExecutor
from edera.workflow.executors import ManagedWorkflowExecutor
from edera.workflow.executors import MonitoringWorkflowExecutor
from edera.workflow.processors import TagFilter
from edera.workflow.processors import TargetCacher
from edera.workflow.processors import TargetLocker
from edera.workflow.processors import TargetPostChecker
from edera.workflow.processors import TaskFreezer
from edera.workflow.processors import TaskRanker
from edera.workflow.processors import WorkflowNormalizer
from edera.workflow.processors import WorkflowTrimmer


@six.add_metaclass(abc.ABCMeta)
class Daemon(object):
    """
    A daemon that builds and executes workflows on regular basis.

    The daemon consists of three modules: $prelude, $main, and $support.
    The $support module runs in parallel with the other two.
    The $prelude module must finish successfully in order for the $main module to start running.

    Each module provides a seed function that generates a root task of the workflow to be executed
    at a particular moment in time.
    It also specifies schedules for different tags (along with $None).
    Each specified tag is handled in a separate process.
    The $builder persistently re-builds the workflow and $executor instances repeatedly attempt
    to execute it.
    Only $prelude's workflows can actually finish.

    The daemon handles SIGINT/SIGTERM signals and knows how to stop gracefully.
    However, you should avoid having active background threads while running the daemon.
    This may lead to a deadlock (see documentation for $ProcessWorker for details).

    Attributes:
        autotester (Optional[DaemonAutoTester]) - the auto-tester used to testify workflows
            Only the $main module will be auto-tested.
        builder (WorkflowBuilder)
        cache (Optional[Storage]) - the storage used to cache targets
        executor (WorkflowExecutor)
        interruption_timeout (TimeDelta) - time to wait for interrupted executors to terminate
        locker (Optional[Locker]) - the locker used to deduplicate task execution
        main (DaemonModule)
        manager (ContextManager) - the context manager that controls both building and execution
        monitor (Optional[Storage]) - the storage used for monitoring purposes
        postprocessors (Iterable[WorkflowProcessor]) - the sequence of processors applied after
                filtering by tag
        prelude (Optional[StaticDaemonModule])
        preprocessors (Iterable[WorkflowProcessor]) - the sequence of processors applied before
                filtering by tag
        support (Optional[DaemonModule])

    Constants:
        CONSUMER_CAPACITY (Integer) - the capacity of the consumer that serves monitoring agents
        CONSUMER_BACKOFF (TimeDelta) - the backoff of the consumer that serves monitoring agents

    See also:
        $DaemonAutoTester
        $DaemonModule
        $DaemonSchedule

    WARNING!
        Avoid having active background threads when starting the daemon.
        See $ProcessWorker's documentation for details.
    """

    CONSUMER_CAPACITY = 1000
    CONSUMER_BACKOFF = datetime.timedelta(seconds=1)

    def __init__(self):
        self.__consumer = InterProcessConsumer(
            lambda kv: self.monitor.put(*kv),
            self.CONSUMER_CAPACITY,
            self.CONSUMER_BACKOFF)

    @property
    def autotester(self):
        pass

    @property
    def builder(self):
        return WorkflowBuilder()

    @property
    def cache(self):
        pass

    @property
    def executor(self):
        result = BasicWorkflowExecutor()
        if self.monitor is not None:
            host_name = socket.getfqdn()
            process_name = multiprocessing.current_process().name
            thread_name = threading.current_thread().name
            agent_name = ":".join([host_name, process_name, thread_name])
            agent = MonitoringAgent(agent_name, self.monitor, self.__consumer)
            result = MonitoringWorkflowExecutor(result, agent)
        result = ManagedWorkflowExecutor(result, self.manager)
        return result

    @property
    def interruption_timeout(self):
        return datetime.timedelta(minutes=1)

    @property
    def locker(self):
        pass

    @abc.abstractproperty
    def main(self):
        pass

    @property
    def manager(self):
        return CascadeManager([])

    @property
    def monitor(self):
        pass

    @property
    def postprocessors(self):
        if self.cache is not None:
            yield TargetCacher(self.cache)
        yield WorkflowTrimmer()
        yield TargetPostChecker()
        if self.locker is not None:
            yield TargetLocker(self.locker)
        yield TaskRanker()

    @property
    def prelude(self):
        pass

    @property
    def preprocessors(self):
        yield TaskFreezer()
        yield WorkflowNormalizer()

    @routine
    def run(self):
        """
        Start the daemon.
        """

        def check_interruption_flag():
            if interruption_flag.raised:
                raise SystemExit("SIGINT/SIGTERM received")

        multiprocessing.current_process().name = "-"
        threading.current_thread().name = "-"
        interruption_flag = InterProcessFlag()
        with Sasha({signal.SIGINT: interruption_flag.up, signal.SIGTERM: interruption_flag.up}):
            logging.getLogger(__name__).info("Daemon starting")
            try:
                yield self.__run[check_interruption_flag].defer()
            except SystemExit as error:
                logging.getLogger(__name__).info("Daemon stopped: %s", error)

    @property
    def support(self):
        pass

    @routine
    def __build(self, seeder, testable, tag, box):
        if testable and self.autotester is not None:
            root = self.autotester.seed(seeder)
        else:
            root = seeder(edera.helpers.now())
        workflow = self.builder.build(root)
        with self.manager:
            if testable and self.autotester is not None:
                yield
                self.autotester.testify(workflow)
            for processor in self.preprocessors:
                yield deferrable(processor.process).defer(workflow)
            TagFilter(tag).process(workflow)
            for processor in self.postprocessors:
                yield deferrable(processor.process).defer(workflow)
        box.put(workflow)

    @routine
    def __execute(self, box, completion_flag):
        while True:
            workflow = box.get()
            if workflow is not None:
                break
            yield edera.helpers.sleep.defer(datetime.timedelta(seconds=1))
        yield deferrable(self.executor.execute).defer(workflow)
        completion_flag.up()

    @routine
    def __run(self):

        @routine
        def run_consumer():
            yield self.__consumer.run.defer()

        @routine
        def run_watcher():
            if self.monitor is not None:
                yield MonitorWatcher(self.monitor).run.defer(delay=datetime.timedelta(seconds=1))

        @routine
        def run_support():
            if self.support is not None:
                yield self.__run_module.defer("support", self.support)

        @routine
        def run_main():
            if self.prelude is not None:
                yield self.__run_module.defer("prelude", self.prelude, sustain=False)
            regular = self.autotester is None
            yield self.__run_module.defer("main", self.main, sustain=regular, testable=True)
            self.autotester.finish()

        timeout = 2 * self.interruption_timeout
        yield MultiProcessInvoker(
            {
                "consumer": run_consumer,
                "watcher": run_watcher,
                "launcher#support": run_support,
                "launcher#main": run_main,
            },
            interruption_timeout=timeout).invoke.defer()

    @routine
    def __run_module(self, name, module, sustain=True, testable=False):
        timeout = 2 * self.interruption_timeout
        yield MultiProcessInvoker(
            {
                (name if tag is None else name + "#" + tag): self.__run_module_branch.fix(
                    tag,
                    module.seed,
                    module.scheduling[tag],
                    sustain,
                    testable)
                for tag in module.scheduling
            },
            interruption_timeout=timeout).invoke.defer()

    @routine
    def __run_module_branch(self, tag, seeder, schedule, sustain, testable):

        def check_completion_flag():
            if not sustain and completion_flag.raised:
                raise SystemExit("finished successfully")

        box = SimpleBox()
        completion_flag = InterThreadFlag()
        timeout = 2 * self.interruption_timeout
        yield MultiThreadedInvoker(
            {
                "builder": PersistentInvoker(
                    self.__build.fix(seeder, testable, tag, box),
                    delay=schedule.building_delay).invoke,
                "executor": MultiThreadedInvoker.replicate(
                    PersistentInvoker(
                        self.__execute.fix(box, completion_flag),
                        delay=schedule.execution_delay).invoke,
                    schedule.executor_count,
                    prefix="executor-",
                    interruption_timeout=self.interruption_timeout).invoke,
            },
            interruption_timeout=timeout).invoke[check_completion_flag].defer()
