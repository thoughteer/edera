import kazoo.client

from edera.managers import ZooKeeperManager


def test_manager_starts_and_stops_client_on_time(zookeeper):
    zookeeper.stop()
    zookeeper.close()
    with ZooKeeperManager(zookeeper):
        assert zookeeper.state == kazoo.client.KazooState.CONNECTED
    assert zookeeper.state == kazoo.client.KazooState.LOST
    zookeeper.start()
