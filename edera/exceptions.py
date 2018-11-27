"""
This module declares all custom exception classes.
"""

import edera.helpers


class Error(Exception):
    """
    The base class for all exceptions within Edera.
    """


class ExcusableError(Error):
    """
    The base class for all "excusable" errors.

    They barely deserve a warning.
    """


class UndefinedParameterError(Error):
    """
    You did not pass a required parameter.
    """

    def __init__(self, name):
        """
        Args:
            name (String) - the name of the parameter
        """
        Error.__init__(self, "parameter `%s` is undefined" % name)


class UnknownParameterError(Error):
    """
    You passed an unknown parameter.
    """

    def __init__(self, name):
        """
        Args:
            name (String) - the name of the parameter
        """
        Error.__init__(self, "passed unknown parameter `%s`" % name)


class ValueQualificationError(Error):
    """
    You passed an invalid value the a qualifier.
    """

    def __init__(self, value, explanation):
        """
        Args:
            value (Any) - the invalid value
            explanation (String) - what's gone wrong
        """
        Error.__init__(self, "value %r was not qualified: %s" % (value, explanation))


class LockAcquisitionError(ExcusableError):
    """
    We failed to acquire a lock for a key.
    """

    def __init__(self, key):
        """
        Args:
            key (String) - the key
        """
        ExcusableError.__init__(self, "lock for key `%s` has been already acquired" % key)


class LockRetentionError(ExcusableError):
    """
    We failed to retain a lock.
    """

    def __init__(self, key):
        """
        Args:
            key (String) - the key of the lock
        """
        ExcusableError.__init__(self, "lock for key `%s` was lost" % key)


class RequisiteConformationError(Error):
    """
    You used an invalid object as a requisite for a task.
    """

    def __init__(self, requisite):
        """
        Args:
            requisite (Any) - the invalid object
        """
        Error.__init__(self, "cannot conform %r" % requisite)


class CircularDependencyError(Error):
    """
    You provided a graph with a cycle.

    Attributes:
        cycle (List[Any]) - the detected cycle
    """

    def __init__(self, cycle):
        """
        Args:
            cycle (List[Any]) - the detected cycle
        """
        message = "circular dependency detected: %s ..." % edera.helpers.render(cycle)
        Error.__init__(self, message)
        self.cycle = cycle


class TargetVerificationError(Error):
    """
    Execution of your task didn't make its target come true.

    Attributes:
        task (Task) - the broken task
    """

    def __init__(self, task):
        """
        Args:
            task (Task) - the broken task
        """
        message = "target %r of task %r is false after execution" % (task.target, task)
        Error.__init__(self, message)
        self.task = task


class InvocationError(Error):
    """
    The base class for all invocation errors within invokers.
    """


class ExcusableInvocationError(ExcusableError):
    """
    The base class for all excusable invocation errors within invokers.
    """


class MasterSlaveInvocationError(InvocationError):
    """
    Some of the slave workers failed for some reason.

    Attributes:
        failed_slaves (List[Worker]) - failed slave workers
    """

    def __init__(self, failed_slaves):
        """
        Args:
            failed_slaves (List[Worker]) - failed slave workers
        """
        message = "some of the slaves failed: %s" % edera.helpers.render(failed_slaves)
        InvocationError.__init__(self, message)
        self.failed_slaves = failed_slaves


class ExcusableMasterSlaveInvocationError(ExcusableInvocationError):
    """
    Some of the slave workers stopped for some good reason.

    Attributes:
        stopped_slaves (List[Worker]) - stopped slave workers
    """

    def __init__(self, stopped_slaves):
        """
        Args:
            stopped_slaves (List[Worker]) - stopped slave workers
        """
        message = "some of the slaves stopped: %s" % edera.helpers.render(stopped_slaves)
        ExcusableInvocationError.__init__(self, message)
        self.stopped_slaves = stopped_slaves


class WorkflowExecutionError(Error):
    """
    There were inexcusable errors during execution.

    Attributes:
        failed_tasks (List[Task]) - failed tasks
    """

    def __init__(self, failed_tasks):
        """
        Args:
            failed_tasks (List[Task]) - failed tasks
        """
        message = "some of the tasks failed: %s" % edera.helpers.render(failed_tasks)
        Error.__init__(self, message)
        self.failed_tasks = failed_tasks


class ExcusableWorkflowExecutionError(ExcusableError):
    """
    There were excusable (and no inexcusable) errors during execution.

    Attributes:
        stopped_tasks (List[Task]) - stopped tasks
    """

    def __init__(self, stopped_tasks):
        """
        Args:
            stopped_tasks (List[Task]) - stopped tasks
        """
        message = "some of the tasks stopped: %s" % edera.helpers.render(stopped_tasks)
        ExcusableError.__init__(self, message)
        self.stopped_tasks = stopped_tasks


class WorkflowNormalizationError(Error):
    """
    You described a workflow that cannot be normalized.
    """


class WorkflowTestificationError(Error):
    """
    You provided an invalid test/stub definition.
    """


class StorageOperationError(Error):
    """
    We failed to operate your storage.
    """


class MonitorInconsistencyError(Error):
    """
    Monitoring data has been corrupted.

    Perhaps, you're running multiple instances of $MonitorWatcher at the same time.
    That is a big no-no.
    Use a locker to prevent parallel execution.
    """
