import abc

import six


@six.add_metaclass(abc.ABCMeta)
class Linearizer(object):
    """
    An interface for graph linearizers.

    Linearizers perform topological ordering of graphs.
    As simple as it sounds.
    """

    @abc.abstractmethod
    def linearize(self, graph):
        """
        Linearize the graph.

        Doesn't mutate the graph.

        Args:
            graph (Graph)

        Returns:
            List[Any] - the sorted graph items

        Raises:
            CircularDependencyError if there is a cycle in the graph
        """
