import pytest

from edera.exceptions import CircularDependencyError


def test_linearizer_performs_topological_ordering(valid_graph, linearizer):
    ordering = linearizer.linearize(valid_graph)
    assert set(ordering) == set(valid_graph)
    for index, item in enumerate(ordering):
        assert valid_graph[item].parents <= set(ordering[:index])


def test_linearizer_detects_circular_dependencies(invalid_graph, linearizer):
    with pytest.raises(CircularDependencyError) as info:
        linearizer.linearize(invalid_graph)
    assert tuple(info.value.cycle) in {(2, 5, 7), (5, 7, 2), (7, 2, 5)}


def test_linearizer_can_handle_really_deep_graphs(really_deep_graph, linearizer):
    assert linearizer.linearize(really_deep_graph) == list(range(10000))
