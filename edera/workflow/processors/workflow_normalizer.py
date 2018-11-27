import collections
import itertools
import logging

import sympy
from sympy.logic import boolalg as sympyboolalg
from sympy.logic import inference as sympyinference

import edera.condition
import edera.helpers

from edera.exceptions import CircularDependencyError
from edera.exceptions import WorkflowNormalizationError
from edera.graph import Graph
from edera.linearizers import DFSLinearizer
from edera.task import TaskWrapper
from edera.workflow.processor import WorkflowProcessor


class WorkflowNormalizer(WorkflowProcessor):
    """
    A workflow processor that attempts to "normalize" task targets.

    The easiest example of an unnormalized workflow is the following pipeline:
        "GenerateFile" (file exists) > "UploadFile" (URL exists) > "RemoveFile" (file not exists)
    Targets of "GenerateFile" and "RemoveFile", obviously, contradict, making it impossible
    to optimize the workflow by selective target checks.
    However, a normalizer is able to "normalize" those targets as follows:
        "GenerateFile" => (file exists OR URL exists)
        "RemoveFile" => (file not exists AND URL exists)
    These conjunctive and disjunctive target corrections can be generalized to arbitrary workflows.

    There are several drawbacks of this approach to consider:
      - you need to provide enough information about targets through condition invariants
      - some workflows can't be normalized (you need better target design in this case)
      - it may take a lot of time, depending on the nature of the constraints
    """

    @classmethod
    def check(cls, workflow):
        """
        Check whether the workflow is normalized.

        Args:
            workflow (Graph) - a workflow to check

        Returns:
            Boolean - $True iff the workflow is normalized
        """
        try:
            targets = _get_graph_of_targets(workflow)
        except CircularDependencyError:
            return False
        return _check_targets(targets)[1]

    def process(self, workflow):
        """
        Raises:
            WorkflowNormalizationError if the workflow can't be normalized
        """
        try:
            targets = _get_graph_of_targets(workflow)
        except CircularDependencyError as error:
            raise WorkflowNormalizationError(error)
        constraint, normalized = _check_targets(targets)
        if normalized:
            return
        logging.getLogger(__name__).debug("Trying to normalize the workflow")
        constraint_atoms = constraint.atoms()
        pivot = {target for target in targets if target.symbol not in constraint_atoms}
        roots = {target for target in targets if not targets[target].parents}
        leafs = {target for target in targets if not targets[target].children}
        indices = {target: index for index, target in enumerate(targets)}
        alpha = {
            target: [
                sympy.Symbol("alpha/%d/0" % indices[target]),
                sympy.Symbol("alpha/%d/1" % indices[target]),
            ]
            for target in targets
            if target not in pivot
        }
        gamma = {
            target: {
                child: sympy.Symbol("gamma/%d-%d" % (indices[target], indices[child]))
                for child in targets[target].children
                if target not in pivot or child not in pivot
            }
            for target in targets
        }
        objective = (
            constraint.xreplace({target.symbol: alpha[target][0] for target in alpha}) &
            constraint.xreplace({target.symbol: alpha[target][1] for target in alpha}) &
            sympyboolalg.And(
                *(
                    ~alpha[target][0] | sympyboolalg.Or(
                        *(~gamma[parent][target] for parent in targets[target].parents))
                    for target in alpha
                )) &
            sympyboolalg.And(
                *(
                    alpha[target][1] | sympyboolalg.Or(
                        *(gamma[target][child] for child in targets[target].children))
                    for target in alpha
                )) &
            sympyboolalg.And(*(~alpha[target][0] | alpha[target][1] for target in alpha))
        )
        objective = objective.xreplace({alpha[target][0]: False for target in roots - pivot})
        objective = objective.xreplace({alpha[target][1]: True for target in leafs - pivot})
        logging.getLogger(__name__).debug("Solving SAT with %d variables", len(objective.atoms()))
        solution = sympyinference.satisfiable(objective)
        if solution is False:
            raise WorkflowNormalizationError("SAT has no solutions: %r" % objective)
        # conjunctively correctable targets
        ccts = {
            target
            for target in alpha
            if target not in roots and solution[alpha[target][0]]
        }
        # disjunctively correctable targets
        dcts = {
            target
            for target in alpha
            if target not in leafs and not solution[alpha[target][1]]
        }
        corrections = _get_target_corrections(targets, ccts, dcts)
        if ccts or dcts:
            raise WorkflowNormalizationError(
                "some target corrections are not feasible: " + edera.helpers.render(ccts | dcts))
        logging.getLogger(__name__).debug(
            "Correcting targets: %s" % edera.helpers.render(corrections))
        for task in workflow:
            if task.target is None or task.target not in corrections:
                continue
            workflow.replace(TargetOverridingTaskWrapper(task, corrections[task.target]))


class TargetOverridingTaskWrapper(TaskWrapper):
    """
    A task wrapper that overrides its target.
    """

    def __init__(self, base, target):
        """
        Args:
            base (Task) - a base task
            target (Optional[Condition]) - a condition to override the target with
        """
        TaskWrapper.__init__(self, base)
        self.__target = target

    @property
    def target(self):
        return self.__target


def _check_targets(targets):
    constraint = edera.condition.derive_constraint(targets)
    constraint_atoms = constraint.atoms()
    constraint_function = sympy.Lambda(constraint_atoms, constraint)
    can_be_fully_complete = constraint_function(*[True for _ in constraint_atoms])
    can_be_fully_incomplete = constraint_function(*[False for _ in constraint_atoms])
    normalized = can_be_fully_complete and can_be_fully_incomplete
    return (constraint, normalized)


def _get_graph_of_targets(workflow):
    result = Graph()
    parent_targets_by_task = {}
    for task in DFSLinearizer().linearize(workflow):
        parent_target_groups = (
            parent_targets_by_task[parent] if parent.target is None else [parent.target]
            for parent in (workflow[parent].item for parent in workflow[task].parents)
        )
        parent_targets = set(itertools.chain(*parent_target_groups))
        if task.target is None:
            parent_targets_by_task[task] = parent_targets
            continue
        if task.target not in result:
            result.add(task.target)
        for parent_target in parent_targets:
            result.link(parent_target, task.target)
    DFSLinearizer().linearize(result)  # make sure there are no cycles
    return result


def _get_target_corrections(targets, ccts, dcts):
    pivot = set(targets) - ccts - dcts
    result = {target: target for target in pivot}
    deque = collections.deque(pivot)
    while deque:
        target = deque.popleft()
        for child in targets[target].children:
            if child in ccts:
                result[child] = child & result[target]
                ccts.remove(child)
                deque.append(child)
        for parent in targets[target].parents:
            if parent in dcts:
                result[parent] = parent | result[target]
                dcts.remove(parent)
                deque.append(parent)
    return {target: result[target] for target in result if target not in pivot}
