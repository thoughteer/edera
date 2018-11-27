from edera.graph import Graph
from edera.heap import Heap
from edera.requisites import Include


class WorkflowBuilder(object):
    """
    A workflow builder.

    Transforms a task into a workflow by satisfying its requisite.

    See also:
        $Requisite
        $Task
        $WorkflowProcessor
    """

    def build(self, task):
        """
        Transform the task into a workflow.

        Args:
            task (Task)

        Returns:
            Graph
        """
        result = Graph()
        heap = Heap()  # this keeps all known unsatisfied requisites
        stack = []  # this keeps non-empty requisite generators
        request = (None, Include(task))
        heap.push(request, request[1].priority)
        while heap or stack:
            if not stack or heap and heap.top[1].priority > stack[-1][1]:
                requisitor, requisite = heap.pop()
                subrequests = requisite.satisfy(requisitor, result)
                if subrequests is not None:
                    stack.append((iter(subrequests), requisite.priority))
                continue
            request = next(stack[-1][0], None)
            if request is None:
                stack.pop()
                continue
            requisitor, requisite = request
            if requisite is None:
                continue
            requisitor = None if requisitor is None else result[requisitor].item
            request = (requisitor, requisite)
            heap.push(request, request[1].priority)
        return result
