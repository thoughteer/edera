import collections
import operator

import six

from edera.disjointset import DisjointSet


class Graph(object):
    """
    An implementation of the directed graph.

    A graph consists of nodes and directed edges.
    Each node holds:
      - an item, which is used to find the node in the graph
      - an annotation, which is used to store additional information
      - the set of its children and the set of its parents (items, not nodes)
    Each edge connects two nodes (once).

    Graph items must be hashable and comparable.

    Examples:
        >>> graph = Graph()  # create an empty graph
        >>> graph.add("A")  # now item "A" is stored in a node
        >>> graph.add("B")  # now item "B" is stored in another node
        >>> graph.link("A", "B")  # now there is an edge from "A" to "B"
        >>> "A" in graph  # check whether an item is in the graph
        True
        >>> isinstance(graph["A"], GraphNode)  # access the node by item
        True
        >>> graph["A"]["put here"] = "anything you want"  # annotate
        >>> graph["A"]["put here"]
        'anything you want'
        >>> graph["A"].children
        {'B'}
        >>> graph["B"].parents
        {'A'}
        >>> set(graph)  # iterate over graph items
        {'A', 'B'}
        >>> len(graph)  # get the number of nodes
        2
        >>> isinstance(graph.clone(), Graph)  # create a shallow copy of the graph
        True
        >>> graph.remove("A")  # remove an item (removes all adjacent edges as well)
        >>> set(graph)
        {'B'}
        >>> list(map(id, graph))  # take a look at the item ids
        [140101652783512]
        >>> graph.replace(u"B")  # replace "B" with a different (but equal) object
        >>> list(map(id, graph))  # take a look at the item ids now
        [140101581973808]
        >>> set(graph)  # allows to wrap node items in-place
        {u'B'}
    """

    def __contains__(self, item):
        """
        Check whether the item is in the graph.

        Args:
            item (Any) - an item

        Returns:
            Boolean - True iff the item is in the graph
        """
        return item in self.__node_map

    def __getitem__(self, item):
        """
        Get the node holding the given item.

        Args:
            item (Any) - an item

        Returns:
            GraphNode

        Raises:
            AssertionError if the item is not in the graph

        See also:
            $GraphNode
        """
        assert item in self
        return self.__node_map[item]

    def __init__(self):
        self.__node_map = {}

    def __iter__(self):
        """
        Get an iterator over graph items.

        Returns:
            Iterator[Any]
        """
        return (node.item for node in six.itervalues(self.__node_map))

    def __len__(self):
        """
        Get the number of nodes in the graph.

        Returns:
            Integer
        """
        return len(self.__node_map)

    def add(self, item):
        """
        Add the item to the graph.

        Creates a new node that holds the given item.
        The node will have an empty annotation and no edges attached.

        Args:
            item (Any) - an item

        Raises:
            AssertionError if the item is already in the graph
        """
        assert item not in self
        self.__node_map[item] = GraphNode(item)

    def clone(self):
        """
        Create a shallow copy of the graph.

        Returns:
            Graph
        """
        result = Graph()
        for item in self:
            result.add(item)
            result[item].annotation = dict(self[item].annotation)
            result[item].parents = set(self[item].parents)
            result[item].children = set(self[item].children)
        return result

    def clusterize(self):
        """
        Split the graph into connected components.

        Returns:
            List[Set[Any]] - clusterized graph items
        """
        indices = {
            item: index
            for index, item in enumerate(self)
        }
        clusters = DisjointSet(len(self))
        for item in self:
            index = indices[item]
            for parent in self[item].parents:
                clusters.merge(index, indices[parent])
        result = collections.defaultdict(set)
        for item in self:
            result[clusters.find(indices[item])].add(item)
        return list(six.itervalues(result))

    def link(self, from_item, to_item):
        """
        Connect the two items with an edge.

        Same items can be linked multiple times.

        Args:
            from_item (Any) - a "from" item
            to_item (Any) - a "to" item

        Raises:
            AssertionError if either $from_item or $to_item is not in the graph
        """
        assert from_item in self
        assert to_item in self
        self.__node_map[to_item].parents.add(from_item)
        self.__node_map[from_item].children.add(to_item)

    def remove(self, *items):
        """
        Remove the items from the graph.

        Removes all the adjacent edges as well.

        Args:
            items (Tuple[Any...]) - graph items

        Raises:
            AssertionError if some of the items are not in the graph
        """
        items = set(items)
        for item in items:
            assert item in self
        for item in items:
            del self.__node_map[item]
        for item in self:
            node = self[item]
            node.parents -= items
            node.children -= items

    def replace(self, item):
        """
        Replace the equivalent item in the graph.

        Finds an item in the graph that is equal to the given item, then replaces it with
        the given item.

        Args:
            item (Any) - an item

        Raises:
            AssertionError if the item is not in the graph
        """
        assert item in self
        self.__node_map[item].item = item

    def trace(self, item, direction):
        """
        Find all ancestors/descendants of the item.

        Args:
            item (Any) - a source item
            direction (String) - either "A" (for ancestors) or "D" (for descendants)
                Determines the tracing direction.

        Returns:
            Set[Any] - the set of ancestor/descendant items
                The source item itself is not included.

        Raises:
            AssertionError if the item is not in the graph
        """
        assert direction in ("A", "D")
        selector = operator.attrgetter("parents" if direction == "A" else "children")
        result = set()
        stack = list(selector(self[item]))
        while stack:
            relative = stack.pop()
            if relative in result:
                continue
            result.add(relative)
            stack.extend(selector(self[relative]))
        return result


class GraphNode(object):
    """
    A node of a graph.

    Note, that $parents and $children are just equivalent to corresponding items, so make sure
    you access actual parent/child items as

        >>> parent = next(iter(graph[item].parents))  # get an equivalent item
        >>> actual_parent = graph[parent].item  # get the actual parent item

    Attributes:
        item (Any) - the contained item
        annotation (Mapping[String, Any]) - the annotation
        parents (Set[Any]) - the set of parent items (or equivalents)
        children (Set[Any]) - the set of child items (or equivalents)

    See also:
        $Graph
    """

    __slots__ = ("item", "annotation", "parents", "children")

    def __getitem__(self, key):
        """
        Get an annotation by key.

        This is just a shortcut for `self.annotation[key]`.

        Args:
            key (String)

        Returns:
            Any
        """
        return self.annotation[key]

    def __init__(self, item):
        """
        Args:
            item (Any) - an item to hold

        See also:
            $Graph.add
        """
        self.item = item
        self.annotation = {}
        self.parents = set()
        self.children = set()

    def __setitem__(self, key, value):
        """
        Set an annotation for the key.

        This is just a shortcut for `self.annotation[key] = value`.

        Args:
            key (String)
            value (Any)
        """
        self.annotation[key] = value
