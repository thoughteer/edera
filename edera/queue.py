class Queue(object):
    """
    A data structure that allows to traverse a graph of ranked items.

    You should either accept or discard an item from the queue in order to move to the next one.
    When an item gets discarded, all its descendants get discarded as well.

    Doesn't mutate the original graph.

    Examples:
        >>> graph = Graph()  # create an empty graph and start filling it
        >>> graph.add("1")
        >>> graph.add("2")
        >>> graph.add("3")
        >>> graph.link("1", "2")
        >>> graph.link("1", "3")
        >>> graph["1"]["rank"] = 1
        >>> graph["2"]["rank"] = 2
        >>> graph["3"]["rank"] = 3
        >>> # first let's accept all
        >>> queue = Queue(graph)
        >>> queue.pick()
        "1"
        >>> queue.accept()
        >>> queue.pick()
        "2"
        >>> queue.accept()
        >>> queue.pick()
        "3"
        >>> queue.accept()
        >>> not queue
        True
        >>> # now let's discard "1"
        >>> queue = Queue(graph)
        >>> queue.pick()
        "1"
        >>> queue.discard()
        >>> not queue  # since "2" and "3" are linked with "1"
        True
    """

    def __init__(self, graph):
        """
        Args:
            graph (Graph) - a graph to iterate over
                All items must be annotated with `rank`.

        Raises:
            AssertionError if some of the items aren't ranked
        """
        assert all("rank" in graph[item].annotation for item in graph)
        self.__items = sorted(graph, key=(lambda item: graph[item]["rank"]))[::-1]
        self.__item_children_map = {item: graph[item].children for item in self.__items}
        self.__discard = set()

    def __iter__(self):
        """
        Get an iterator over the rest of the queue in ranking order.

        Returns:
            Iterator[Any]
        """
        return reversed(self.__items)

    def __len__(self):
        """
        Get the number of items left in the queue.

        Returns:
            Integer
        """
        return len(self.__items)

    def accept(self):
        """
        Accept the current item.

        Raises:
            AssertionError if there are no more items left
        """
        assert self
        self.__items.pop()
        self.__skip_discarded()

    def discard(self):
        """
        Discard the current item.

        Raises:
            AssertionError if there are no more items left
        """
        assert self
        self.__discard.add(self.__items[-1])
        self.__skip_discarded()

    def pick(self):
        """
        Get the current item.

        Neither accepts nor discards the item, just allows to access it.

        Returns:
            Any

        Raises:
            AssertionError if there are no more items left
        """
        assert self
        return self.__items[-1]

    def __skip_discarded(self):
        while self.__items:
            item = self.__items[-1]
            if item not in self.__discard:
                break
            self.__discard.update(self.__item_children_map[item])
            self.__items.pop()
