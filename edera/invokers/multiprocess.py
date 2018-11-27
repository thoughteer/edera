from edera.flags import InterProcessFlag
from edera.invokers.masterslave import MasterSlaveInvoker
from edera.workers import ProcessWorker


class MultiProcessInvoker(MasterSlaveInvoker[ProcessWorker, InterProcessFlag]):
    """
    A master-slave invoker that runs actions in separate (forked) processes.

    See also:
        $MasterSlaveInvoker
        $ProcessWorker

    WARNING!
        Please, carefully read $ProcessWorker's documentation before using this invoker.
    """
