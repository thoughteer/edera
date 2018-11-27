class DisjointSet(object):
    """
    A simplified implementation of the disjoint-set data structure.

    You can create a set of distinct one-element sets, merge these sets in any order, and find
    the index of the set an element belongs to.

    Since this disjoint-set data structure operates element indices instead of actual elements,
    you only need to specify the size of the whole set at the creation time.

    Examples:
        >>> ds = DisjointSet(3)  # {{0}, {1}, {2}}
        >>> ds.find(0), ds.find(1), ds.find(2)
        (0, 1, 2)
        >>> ds.merge(0, 2)  # {{0, 2}, {1}}
        >>> ds.find(0) == ds.find(2)
        True
        >>> ds.find(0) == ds.find(1)
        False
        >>> ds.merge(1, 2)  # {{0, 1, 2}}
        >>> ds.find(0) == ds.find(1) == ds.find(2)
        True
    """

    def __init__(self, size):
        """
        Args:
            size (Integer) - the size of the disjoint-set

        Raises:
            AssertionError if $size is negative

        The elements of the disjoint-set are {0, 1, .., $size - 1}.
        Initially, each element is contained within its own set.
        """
        assert size >= 0
        self.__elements = list(map(_DisjointSetElement, range(size)))
        self.__size = size

    def find(self, x):
        """
        Find the index of the set that contains the given element.

        Args:
            x (Integer) - an element

        Returns:
            Integer - the index of the containing set
                Such set indices are equal iff the corresponding sets are equal.

        Raises:
            AssertionError if $x is not an element of the disjoint-set
        """
        assert 0 <= x < self.__size
        parent = self.__elements[x].parent
        if parent != x:
            parent = self.__elements[x].parent = self.find(parent)
        return parent

    def merge(self, x, y):
        """
        Merge the containing sets of the given elements.

        Args:
            x (Integer) - an element
            y (Integer) - an element

        Raises:
            AssertionError if either $x or $y is not an element of the disjoint-set
        """
        assert 0 <= x < self.__size
        assert 0 <= y < self.__size
        x_root = self.find(x)
        x_rank = self.__elements[x_root].rank
        y_root = self.find(y)
        y_rank = self.__elements[y_root].rank
        if x_rank < y_rank:
            self.__elements[x_root].parent = y_root
        elif x_rank > y_rank:
            self.__elements[y_root].parent = x_root
        else:
            self.__elements[y_root].parent = x_root
            self.__elements[x_root].rank += 1


class _DisjointSetElement(object):

    def __init__(self, x):
        self.parent = x
        self.rank = 0
