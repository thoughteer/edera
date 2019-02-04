from edera.storages import EmbeddedStorage


def test_embedded_storages_have_independent_keyspaces(inmemory_storage):
    main = EmbeddedStorage(inmemory_storage, "keyspace#1")
    parallel = EmbeddedStorage(inmemory_storage, "keyspace#2")
    main.put("key", "value")
    assert not parallel.get("key")
    parallel.put("key", "value")
    assert len(main.get("key")) == 1
