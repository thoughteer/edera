import six


def test_putting_to_storage_increments_version(storage):
    v = storage.put("my key", "my value #0")
    assert isinstance(v, six.integer_types)
    assert storage.put("my key", "my value #1") > v


def test_storage_puts_and_gets_records_correctly(storage):
    v0 = storage.put("my key #0", "my value #0")
    v1 = storage.put("my key #1", "my value #1")
    v2 = storage.put("my key #0", "my value #2")
    threshold = storage.get("my key #0")[0][0]
    v3 = storage.put("my key #1", "my value #3")
    v4 = storage.put("my key #0", "my value #4")
    assert storage.get("my key #0") == [
        (v4, "my value #4"),
        (v2, "my value #2"),
        (v0, "my value #0"),
    ]
    assert storage.get("my key #1") == [(v3, "my value #3"), (v1, "my value #1")]
    assert storage.get("my key #2") == []
    assert storage.get("my key #0", limit=2) == [(v4, "my value #4"), (v2, "my value #2")]
    assert storage.get("my key #1", limit=1) == [(v3, "my value #3")]
    assert storage.get("my key #0", limit=0) == []
    assert storage.get("my key #0", since=threshold) == [(v4, "my value #4"), (v2, "my value #2")]
    assert storage.get("my key #0", since=threshold, limit=1) == [(v4, "my value #4")]


def test_storage_deletes_records_correctly(storage):
    storage.put("my key #0", "my value #0")
    storage.put("my key #1", "my value #1")
    v2 = storage.put("my key #0", "my value #2")
    v3 = storage.put("my key #1", "my value #3")
    storage.put("my key #0", "my value #4")
    storage.delete("my key #2")
    assert len(storage.get("my key #2")) == 0
    storage.delete("my key #0", till=v2)
    assert len(storage.get("my key #0")) == 2
    storage.delete("my key #1", till=v3)
    assert len(storage.get("my key #1")) == 1
    storage.delete("my key #0")
    assert not storage.get("my key #0")
    storage.delete("my key #1")
    assert not storage.get("my key #1")
