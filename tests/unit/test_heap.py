import pytest

from edera import Heap


def test_heap_is_initially_empty():
    assert not Heap()


def test_pushing_items_increases_heap_size():
    heap = Heap()
    for i in range(1, 6):
        heap.push(str(i), 0)
        assert len(heap) == i


def test_top_of_heap_always_has_highest_priority():
    heap = Heap()
    for i in range(1, 6):
        heap.push(str(i), -i)
        assert heap.top == "1"
    for i in range(1, 6):
        heap.push(str(i), i)
        assert heap.top == str(i)


def test_heap_pops_items_in_correct_order():
    heap = Heap()
    for i in range(1, 6):
        heap.push(str(i), i)
    assert heap.pop() == "5"
    for i in range(5, 10):
        heap.push(str(i), i)
    for i in range(9, 0, -1):
        assert heap.pop() == str(i)
    assert not heap


def test_accessing_empty_heap_gives_assertion_error():
    heap = Heap()
    with pytest.raises(AssertionError):
        return heap.top


def test_popping_from_empty_heap_gives_assertion_error():
    heap = Heap()
    with pytest.raises(AssertionError):
        heap.pop()


def test_heap_ordering_is_stable():
    heap = Heap()
    for i in range(1, 6):
        heap.push(str(i), 0)
    for i in range(6, 10):
        heap.push(str(i), 0)
    for i in range(1, 10):
        assert heap.pop() == str(i)
    assert not heap
