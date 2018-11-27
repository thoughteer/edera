import pytest

from edera import Graph
from edera import Queue


def test_empty_graph_gives_empty_queue():
    graph = Graph()
    assert not Queue(graph)


def test_queue_can_be_iterated_over():
    graph = Graph()
    graph.add(0)
    for item in range(1, 5):
        graph.add(item)
        graph.link(item - 1, item)
    for item in range(5):
        graph[item]["rank"] = item
    queue = Queue(graph)
    queue.accept()
    assert list(queue) == [1, 2, 3, 4]
    assert queue.pick() == 1
    queue.discard()
    assert not list(queue)


def test_picking_queue_items_has_no_side_effects():
    graph = Graph()
    graph.add(0)
    graph[0]["rank"] = 0
    queue = Queue(graph)
    assert len(queue) == 1
    assert queue.pick() == 0
    assert len(queue) == 1
    assert queue.pick() == 0


def test_accepting_queue_item_just_pops_it():
    graph = Graph()
    graph.add(0)
    for item in range(1, 5):
        graph.add(item)
        graph.link(item - 1, item)
    for item in range(5):
        graph[item]["rank"] = item
    queue = Queue(graph)
    for item in range(5):
        assert queue.pick() == item
        queue.accept()
    assert not queue


def test_discarding_queue_item_pops_all_its_descendants_as_well():
    graph = Graph()
    graph.add(0)
    for item in range(1, 5):
        graph.add(item)
        graph.link(item - 1, item)
    graph.add(5)
    for item in range(6, 9):
        graph.add(item)
        graph.link(item - 1, item)
    for item in range(9):
        graph[item]["rank"] = item
    queue = Queue(graph)
    queue.discard()
    assert len(queue) == 4
    assert queue.pick() == 5
    queue.accept()
    assert queue.pick() == 6
    queue.discard()
    assert not queue


def test_empty_queue_can_do_nothing_but_fail():
    graph = Graph()
    graph.add(0)
    graph[0]["rank"] = 0
    queue = Queue(graph)
    queue.accept()
    with pytest.raises(AssertionError):
        queue.pick()
    with pytest.raises(AssertionError):
        queue.accept()
    with pytest.raises(AssertionError):
        queue.discard()
