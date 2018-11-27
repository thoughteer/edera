import datetime


class ZooKeeperManager(object):
    """
    A context manager that starts a given $kazoo.client.KazooClient instance on enter
    and stops/closes it on exit.

    Attributes:
        zookeeper (kazoo.client.KazooClient) - the managed ZooKeeper client
    """

    def __enter__(self):
        self.zookeeper.start(timeout=self.__timeout.total_seconds())

    def __exit__(self, *args):
        self.zookeeper.stop()
        self.zookeeper.close()

    def __init__(self, zookeeper, timeout=datetime.timedelta(seconds=15)):
        """
        Args:
            zookeeper (kazoo.client.KazooClient) - a ZooKeeper client
            timeout (TimeDelta) - a timeout for setting up the connection
        """
        self.zookeeper = zookeeper
        self.__timeout = timeout

    def __repr__(self):
        return "<%s: zk-id %x>" % (self.__class__.__name__, id(self.zookeeper))
