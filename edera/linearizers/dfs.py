from edera.exceptions import CircularDependencyError
from edera.linearizer import Linearizer


class DFSLinearizer(Linearizer):
    """
    A linearizer that uses depth-first search to perform topological ordering.

    This implementation is non-recursive and can handle really deep graphs.
    """

    def linearize(self, graph):
        unexplored = set(graph)
        exploring = []
        passing = set()
        path = []
        stack = []
        while unexplored:
            item = next(iter(unexplored))
            exploring.append((False, item))
            while exploring:
                explored, item = exploring.pop()
                if item not in unexplored:
                    continue
                if explored:
                    unexplored.remove(item)
                    passing.remove(item)
                    path.pop()
                    stack.append(item)
                    continue
                if item in passing:
                    index = path.index(item)
                    raise CircularDependencyError(path[index:])
                exploring.append((True, item))
                passing.add(item)
                path.append(item)
                for child in graph[item].children:
                    if child in unexplored:
                        exploring.append((False, graph[child].item))
        return stack[::-1]
