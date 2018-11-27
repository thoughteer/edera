import functools
import sys


class Routine(object):
    """
    An interruptible function.

    A routine is a special generator function wrapper that allows to interrupt it
    at points where it yields.
    The last yielded value will be used as the return value of the routine.

    To invoke another routine from the core generator function, yield a deferred routine call
    and obtain the result.
    Note that deferred routine calls do not count as actual values.

    Routines can be called as ordinary functions (no need to iterate or employ event loops).
    You can attach an auditor to the routine, and it will be invoked on each yield statement.

    Please, use $routine as a decorator to create routines.

    Examples:
        >>> import time
        >>> @routine
        >>> def sleep(duration):
        >>>     for i in range(duration):
        >>>         yield sleep.defer(i)
        >>>         time.sleep(1)
        >>> def audit():
        >>>     print("Audit!")
        >>> sleep[audit](duration=3)  # 7 yields lead to 7 auditor calls
        Audit!
        Audit!
        Audit!
        Audit!
        Audit!
        Audit!
        Audit!

    See also:
        $routine
    """

    def __call__(self, *args, **kwargs):
        """
        Run the routine.

        Args:
            *args, **kwargs - arguments to pass to the core
        """
        generator = self.__core(*args, **kwargs)
        result = None
        seed, exception = None, None
        while True:
            try:
                feed = generator.send(seed) if exception is None else generator.throw(*exception)
            except StopIteration:
                return result
            if isinstance(feed, DeferredRoutineCall):
                try:
                    seed = feed.carry()
                except BaseException:
                    exception = sys.exc_info()
                    continue
            else:
                result = feed
            exception = None

    def __get__(self, owner, owner_type=None):
        if owner is None:
            return self
        return self.__class__(functools.partial(self.__core, owner))

    def __getitem__(self, auditor):
        """
        Attach the auditor to the routine.

        Args:
            auditor (Callable[[], Any]) - an auditor function

        Returns:
            Routine
        """

        def core(*args, **kwargs):
            generator = self.__core(*args, **kwargs)
            seed, exception = None, None
            while True:
                feed = generator.send(seed) if exception is None else generator.throw(*exception)
                if isinstance(feed, DeferredRoutineCall):
                    feed.instance = feed.instance[auditor]
                try:
                    auditor()
                    seed = yield feed
                except BaseException:
                    exception = sys.exc_info()
                else:
                    exception = None

        return self.__class__(core)

    def __init__(self, core):
        """
        Args:
            core (GeneratorFunction[Any...]) - a core generator function
                Methods are also supported.
        """
        self.__core = core

    def defer(self, *args, **kwargs):
        """
        Defer the routine call.

        Args:
            *args, **kwargs - arguments to pass to the routine

        Returns:
            DeferredRoutineCall
        """
        return DeferredRoutineCall(self, *args, **kwargs)

    def fix(self, *args, **kwargs):
        """
        Fix some of the routine arguments.

        Args:
            *args, **kwargs - arguments to fix

        Returns:
            Routine
        """
        return self.__class__(functools.partial(self.__core, *args, **kwargs))


class DeferredRoutineCall(object):
    """
    A deferred routine call.

    Contains all necessary information to call the routine.

    Attributes:
        instance (Routine) - a routine to call
        *args, **kwargs - arguments to pass to the routine

    See also:
        $Routine.defer
    """

    def __init__(self, instance, *args, **kwargs):
        """
        Args:
            instance (Routine) - a routine to call
            *args, **kwargs - arguments to pass to the routine
        """
        self.instance = instance
        self.args = args
        self.kwargs = kwargs

    def carry(self):
        """
        Call the routine.

        Returns:
            Any - the result of the call
        """
        return self.instance(*self.args, **self.kwargs)


def deferrable(function):
    """
    Create a fake $Routine instance.

    Has no effect on instances of $Routine.
    Transforms other callable objects into fake non-interruptible routines.

    Can be used to blur the line between ordinary functions and routines.

    Args:
        function (Callable[Any...]) - a function to make deferrable

    Returns:
        Routine
    """

    def pseudocore(*args, **kwargs):
        yield function(*args, **kwargs)

    return function if isinstance(function, Routine) else routine(pseudocore)


def routine(core):
    """
    Create a $Routine instance.

    Args:
        core (GeneratorFunction[Any...]) - a core generator function
            Methods are also supported.

    Returns:
        Routine
    """
    return Routine(core)
