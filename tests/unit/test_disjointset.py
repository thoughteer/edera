import pytest

from edera import DisjointSet


def test_all_subsets_are_initially_disjoint():
    disjointset = DisjointSet(5)
    assert len(set(disjointset.find(index) for index in range(5))) == 5


def test_disjointset_merges_and_finds_subsets_correctly():
    disjointset = DisjointSet(5)
    disjointset.merge(0, 1)
    assert disjointset.find(0) == disjointset.find(1)
    assert disjointset.find(0) != disjointset.find(2)
    disjointset.merge(2, 3)
    disjointset.merge(3, 0)
    assert disjointset.find(1) == disjointset.find(2)
    assert disjointset.find(1) != disjointset.find(4)
    disjointset.merge(3, 4)
    assert len(set(disjointset.find(index) for index in range(5))) == 1


def test_disjointset_fails_to_find_subset_by_invalid_element():
    disjointset = DisjointSet(5)
    with pytest.raises(AssertionError):
        disjointset.find(100)
