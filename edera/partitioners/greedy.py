import edera.partitioner

from edera.partitioner import Partition
from edera.partitioner import Partitioner


class GreedyPartitioner(Partitioner):
    """
    A partitioner based on the greedy coloring algorithm.

    It does use some heuristics though, similar to the Welsh-Powell algorithm.
    """

    def partition(self, items):
        partitions = []
        for item in sorted(items, key=(lambda i: (-len(items[i]), i))):
            mapping = items[item]
            for index, partition in enumerate(partitions):
                if edera.partitioner.mergeable(mapping, partition.mapping):
                    partitions[index].items.add(item)
                    partitions[index].mapping.update(mapping)
                    break
            else:
                partitions.append(Partition({item}, mapping))
        return partitions
