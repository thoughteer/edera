import heapq


class Heap(object):
    """
    An implementation of the max-heap data structure (aka the priority queue).

    A heap is a collection of prioritized items that can be pushed to the heap and then popped
    from the heap in the descending priority order.
    Heaps are initially empty.

    This implementation is stable, i.e. items of equal priority are popped in the FIFO order.

    Attributes:
        top (Any) - the top-priority item of the heap
            Accessing this attribute of an empty heap results in AssertionError.

    Examples:
        >>> heap = Heap()  # create an empty heap
        >>> heap.push("1", 1)  # push "1" with priority 1
        >>> heap.top
        "1"
        >>> heap.push("2", 2)  # push "2" with priority 2
        >>> heap.top
        "2"
        >>> heap.push("0", 0)  # push "0" with priority 0
        >>> heap.top
        "2"
        >>> heap.push("2+", 2)  # push "2+" with priority 2
        >>> len(heap)
        4
        >>> heap.pop()
        "2"
        >>> heap.pop()
        "2+"
        >>> heap.pop()
        "1"
        >>> heap.pop()
        "0"
    """

    def __init__(self):
        self.__items = []
        self.__counter = 0

    def __len__(self):
        """
        Get the size of the heap.

        Returns:
            Integer
        """
        return len(self.__items)

    def pop(self):
        """
        Get and remove the top-priority item from the heap.

        Returns:
            Any - the top-priority item

        Raises:
            AssertionError if the heap is empty
        """
        assert self.__items
        return heapq.heappop(self.__items)[2]

    def push(self, item, priority):
        """
        Add the item with the given priority to the heap.

        Args:
            item (Any) - an item
            priority (Integer) - a priority of the item
        """
        self.__counter += 1
        heapq.heappush(self.__items, (-priority, self.__counter, item))

    @property
    def top(self):
        assert self.__items
        return self.__items[0][2]
