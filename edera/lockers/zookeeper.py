import collections
import contextlib
import logging
import threading

import kazoo.client
import kazoo.exceptions

import edera.helpers

from edera.exceptions import LockAcquisitionError
from edera.locker import Locker


class ZooKeeperLocker(Locker):
    """
    A ZooKeeper-level locker.

    A ZooKeeper-level lock works as an inter-host mutex.

    This locker can handle ZK session expiration and consequent lock losses.
    However, in order to make it work, you need to configure your ZK clients properly.
    Lock owners will be notified as soon as corresponding ZK clients reach the LOST state,
    which happens not quickly enough by default.
    To overcome the issue, you just need to pass a custom $kazoo.retry.KazooRetry object
    as a connection retry policy for your ZK clients.

    Attributes:
        zookeeper (kazoo.client.KazooClient) - the ZK client
        znode (String) - the path of the z-node that holds lock z-nodes

    Constants:
        _MAX_DESCRIPTION_LENGTH (Integer) - the maximum length of key prefixes stored in z-nodes
    """

    _MAX_DESCRIPTION_LENGTH = 8192

    __mutex = threading.Lock()
    __callbacks = collections.defaultdict(set)

    def __init__(self, zookeeper, znode):
        """
        Args:
            zookeeper (kazoo.client.KazooClient) - a ZK client to use
            znode (String) - a base path for lock z-nodes (must point at a non-ephemeral z-node)

        The base path will be created if doesn't exist.
        """
        self.zookeeper = zookeeper
        self.znode = znode

    def __repr__(self):
        return "<%s: zk-id %x - z-node %r>" % (
            self.__class__.__name__,
            id(self.zookeeper),
            self.znode,
        )

    @contextlib.contextmanager
    def lock(self, key, callback=None):
        if callback is not None:
            with self.__mutex:
                if self.zookeeper not in self.__callbacks:
                    self.zookeeper.add_listener(self.__handle_state_change)
                    logging.getLogger(__name__).debug("Registered ZK client %r", self.zookeeper)
                self.__callbacks[self.zookeeper].add(callback)
        try:
            path = "%s/%s" % (self.znode, edera.helpers.sha1(key))
            description = key[:self._MAX_DESCRIPTION_LENGTH].encode("ASCII")
            try:
                self.zookeeper.create(path, value=description, ephemeral=True, makepath=True)
            except kazoo.exceptions.NodeExistsError:
                raise LockAcquisitionError(key)
            except (kazoo.exceptions.ConnectionLoss, kazoo.exceptions.SessionExpiredError):
                self.__notify_about_session_loss()
                raise LockAcquisitionError(key)
            else:
                logging.getLogger(__name__).debug("Created z-node %s with `%s`", path, description)
            try:
                yield
            finally:
                try:
                    self.zookeeper.delete(path)
                except kazoo.exceptions.KazooException:
                    pass
                else:
                    logging.getLogger(__name__).debug("Deleted z-node %s", path)
        finally:
            if callback is not None:
                with self.__mutex:
                    self.__callbacks[self.zookeeper].remove(callback)
                    if not self.__callbacks[self.zookeeper]:
                        del self.__callbacks[self.zookeeper]
                        self.zookeeper.remove_listener(self.__handle_state_change)
                        logging.getLogger(__name__).debug(
                            "Unregistered ZK client %r", self.zookeeper)

    def __handle_state_change(self, state):
        if state == kazoo.client.KazooState.LOST:
            self.__notify_about_session_loss()

    def __notify_about_session_loss(self):
        logging.getLogger(__name__).debug("Session lost for ZK client %r", self.zookeeper)
        for callback in self.__callbacks.get(self.zookeeper, []):
            logging.getLogger(__name__).debug("Invoking the callback: %r", callback)
            callback()
