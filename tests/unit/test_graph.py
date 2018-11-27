import pytest

from edera import Graph


def test_empty_graph_reduces_to_false():
    assert not Graph()


def test_adding_items_increases_graph_size_accordingly():
    graph = Graph()
    for i in range(1, 6):
        graph.add(i)
        assert len(graph) == i


def test_graph_refuses_to_add_existing_items():
    graph = Graph()
    graph.add(1)
    with pytest.raises(AssertionError):
        graph.add(1)


def test_graph_nodes_can_be_linked_multiple_times():
    graph = Graph()
    graph.add("1")
    graph.add("2")
    graph.link("1", "2")
    graph.link("1", "2")


def test_graph_refuses_to_link_nonexisting_nodes():
    graph = Graph()
    with pytest.raises(AssertionError):
        graph.link("1", "2")
    graph.add("1")
    with pytest.raises(AssertionError):
        graph.link("1", "2")


def test_graph_allows_to_check_item_membership():
    graph = Graph()
    graph.add("member")
    assert "member" in graph
    assert "outlier" not in graph


def test_graph_allows_to_get_nodes_by_item_exemplar():
    graph = Graph()
    item = (0, "o")
    with pytest.raises(AssertionError):
        graph[item]
    graph.add(item)
    assert graph[item].item is item
    item_exemplar = (0, "o")
    assert item_exemplar is not item
    assert graph[item_exemplar].item is item


def test_graph_allows_to_replace_items():
    graph = Graph()
    item = (6, "b")
    graph.add(item)
    assert graph[item].item is item
    new_item = (6, "b")
    assert new_item is not item
    graph.replace(new_item)
    assert graph[item].item is new_item


def test_graph_supports_node_annotation():
    graph = Graph()
    item = (3, "E")
    with pytest.raises(AssertionError):
        graph[item]["failed"] = True
    graph.add(item)
    assert graph[item].annotation == {}
    graph[item]["completed"] = True
    assert graph[item]["completed"] is True
    assert graph[item].annotation == {"completed": True}


def test_graph_nodes_keep_track_of_parents_and_children():
    graph = Graph()
    a, b, c = "A", "B", "C"
    graph.add(a)
    graph.add(b)
    graph.add(c)
    assert not graph[a].parents and not graph[a].children
    assert not graph[b].parents and not graph[b].children
    assert not graph[c].parents and not graph[c].children
    graph.link(a, b)
    assert graph[b].parents == {a} and graph[a].children == {b}
    graph.link(b, c)
    assert graph[c].parents == {b} and graph[b].children == {c}
    graph.link(a, c)
    assert graph[a].children == {b, c} and graph[c].parents == {a, b}


def test_graph_allows_to_iterate_over_items():
    graph = Graph()
    graph.add("A")
    graph.add(1)
    graph.add(None)
    assert set(graph) == {"A", 1, None}


def test_graph_can_be_cloned():
    graph = Graph()
    graph.add("A")
    graph.add("B")
    graph.link("A", "B")
    graph["A"][0] = 0
    cloned_graph = graph.clone()
    assert "A" in cloned_graph
    assert "B" in cloned_graph
    assert "A" in cloned_graph["B"].parents
    assert "B" in cloned_graph["A"].children
    assert cloned_graph["A"][0] == 0
    graph["A"][0] = 1
    assert cloned_graph["A"][0] == 0
    graph.add("C")
    assert "C" not in cloned_graph
    graph.link("B", "A")
    assert "B" not in cloned_graph["A"].parents
    assert "A" not in cloned_graph["B"].children


def test_graph_allows_to_remove_items():
    graph = Graph()
    graph.add("A")
    graph.add("B")
    graph.add("C")
    graph.add("D")
    graph.link("A", "B")
    graph.link("B", "C")
    graph.link("C", "D")
    graph.remove("B", "C")
    assert "B" not in graph
    assert "C" not in graph
    assert "A" in graph
    assert not graph["A"].children
    assert "D" in graph
    assert not graph["D"].parents


def test_graph_clusterizes_items_correctly():
    graph = Graph()
    graph.add("A")
    graph.add("B")
    graph.add("C")
    graph.add("D")
    graph.add("E")
    graph.link("A", "B")
    graph.link("C", "B")
    graph.link("D", "E")
    assert sorted(graph.clusterize(), key=len) == [{"D", "E"}, {"A", "B", "C"}]


def test_graph_traces_relatives_correctly():
    graph = Graph()
    graph.add("A")
    graph.add("B")
    graph.add("C")
    graph.add("D")
    graph.add("E")
    graph.link("A", "B")
    graph.link("C", "B")
    graph.link("D", "E")
    graph.link("E", "C")
    graph.link("A", "E")
    assert graph.trace("C", "A") == {"A", "D", "E"}
    assert graph.trace("A", "D") == {"B", "C", "E"}
