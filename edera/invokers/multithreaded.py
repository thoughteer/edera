from edera.flags import InterThreadFlag
from edera.invokers.masterslave import MasterSlaveInvoker
from edera.workers import ThreadWorker


class MultiThreadedInvoker(MasterSlaveInvoker[ThreadWorker, InterThreadFlag]):
    """
    A master-slave invoker that runs actions in separate threads.

    See also:
        $MasterSlaveInvoker
        $ThreadWorker
    """
