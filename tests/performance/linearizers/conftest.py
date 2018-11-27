import pytest

from edera import Graph
from edera.linearizers import DFSLinearizer


@pytest.fixture(params=[1, 10, 100, 1000])
def dense_graph(request):
    result = Graph()
    count = request.param
    for i in range(count):
        result.add(i)
    for i in range(count):
        for j in range(i):
            result.link(i, j)
    return result


@pytest.fixture
def dfs_linearizer():
    return DFSLinearizer()


@pytest.fixture(params=["dfs_linearizer"])
def linearizer(request):
    return request.getfixturevalue(request.param)
