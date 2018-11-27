import pytest

from edera.partitioners import GreedyPartitioner


@pytest.fixture
def items():
    # 0 -- 1 -- 2
    # |    |
    # 3 -- 4
    return {
        0: {0: 0, 1: None, 3: None},
        1: {0: None, 1: 1, 2: None, 4: None},
        2: {1: None, 2: 2},
        3: {0: None, 3: 3, 4: None},
        4: {1: None, 3: None, 4: 4},
    }


@pytest.fixture
def greedy_partitioner():
    return GreedyPartitioner()


@pytest.fixture(params=["greedy_partitioner"])
def partitioner(request):
    return request.getfixturevalue(request.param)
