import abc
import collections

import six


@six.add_metaclass(abc.ABCMeta)
class Partitioner(object):
    """
    An interface for all partitioners.

    Partitioners aim to split a set of items into non-conflicting subsets.
    The conflict between two items is determined by comparing corresponding mappings,
    assigned to each item.
    If there is a common key for which the two mappings have different values,
    then there is a conflict.

    Examples:
        Suppose you need to color graph vertices so that no two adjacent vertices have the same
        color.
        You can just provide the following mapping for each vertex V: V for V, $None for all
        vertices adjacent to V.
        Then you just feed these mappings to a partitioner, e.g.

            >>> # let's describe the graph "1 -- 2 -- 3"
            >>> items = {
            >>>     1: {1: 1, 2: None},
            >>>     2: {2: 2, 1: None, 3: None},
            >>>     3: {3: 3, 2: None},
            >>> }
            >>> print partitioners.partition(items)
            [
                Partition(items=set([2]), mapping={1: None, 2: 2, 3: None}),
                Partition(items=set([1, 3]), mapping={1: 1, 2: None, 3: 3}),
            ]
            >>> # we've got a valid coloring
    """

    @abc.abstractmethod
    def partition(self, items):
        """
        Split the items into non-conflicting subsets (partitions).

        Args:
            items (Mapping[Any, Mapping[Any, Any]]) - an "item-to-mapping" collection

        Returns:
            List[Partition] - each partition holds the items and the joint mapping of the partition
        """


Partition = collections.namedtuple("Partition", ["items", "mapping"])
"""
A partition descriptor.

Attributes:
    items (Set[Any]) - elements of the partition
    mapping (Mapping[Any, Any]) - the joint mapping of the partition
"""


def mergeable(*mappings):
    """
    Check if the mappings are mergeable (i.e. have no conflicts).

    Best performance is achieved when the mappings are sorted by size.

    Args:
        mappings (Tuple[Mapping[Any, Any]...])

    Returns:
        Boolean
    """
    merge = {}
    for mapping in mappings:
        for key in six.iterkeys(mapping if len(mapping) < len(merge) else merge):
            if key in merge and key in mapping and merge[key] != mapping[key]:
                return False
        merge.update(mapping)
    return True
