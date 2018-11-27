from edera.partitioner import Partition


def test_partitioner_splits_items_correctly(partitioner, items):
    partitions = partitioner.partition(items)
    assert len(partitions) == 2
    assert sorted(partitions) == [
        Partition({1, 3}, {0: None, 1: 1, 2: None, 3: 3, 4: None}),
        Partition({0, 2, 4}, {0: 0, 1: None, 2: 2, 3: None, 4: 4}),
    ]
