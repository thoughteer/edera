import logging

import edera.helpers

from edera.condition import ConditionWrapper
from edera.exceptions import WorkflowTestificationError
from edera.partitioners import GreedyPartitioner
from edera.task import TaskWrapper
from edera.testing import AllTestSelector
from edera.testing import Stub
from edera.testing import Test
from edera.workflow.processor import WorkflowProcessor


class WorkflowTestifier(WorkflowProcessor):
    """
    A workflow processor that transforms the workflow into a workflow that auto-tests the original
    workflow.

    It partitions the resulting tests into independent groups, and then assigns different colors
    to different groups.
    Tasks with differing color annotations must not be executed within the same environment.
    You can use $TaskSegregator for environment separation.

    WARNING!
        Doesn't preserve annotations, so consider applying this processor before others.

    See also:
        $TaskSegregator
        $TestableTask
    """

    def __init__(self, cache, selector=AllTestSelector(), partitioner=GreedyPartitioner()):
        """
        Args:
            cache (Storage) - a storage used to store passed tests
                Can be safely shared with the one used for $TargetCacher.
            selector (TestSelector) - a test selector to use
                Default is "all available".
            partitioner (Partitioner) - a partitioner used to group tests and stubs
                Default is the greedy partitioner.
        """
        self.__Test = type.__new__(type, "Test", (Test,), {"cache": cache})
        self.__selector = selector
        self.__partitioner = partitioner

    def process(self, workflow):
        tests = [
            self.__Test(scenario=scenario, subject=task)
            for task in sorted(workflow)
            for scenario in self.__selector.select(workflow, task)
        ]
        logging.getLogger(__name__).debug("Collected %d tests", len(tests))
        substitutions = {test: self.__find_substitution(test, workflow) for test in tests}
        partitions = self.__partitioner.partition(substitutions)
        logging.getLogger(__name__).debug("Split tests into %d groups", len(partitions))
        origin = workflow.clone()
        workflow.remove(*workflow)
        for partition in partitions:
            self.__project(origin, partition, workflow)

    def __find_substitution(self, test, workflow):

        def handle(scenario, subject, stack):
            dependencies = {workflow[parent].item for parent in workflow[subject].parents}
            stubs = scenario.stub(subject, dependencies)
            extra = set(stubs) - dependencies
            if extra:
                raise WorkflowTestificationError(
                    "scenario %r for subject %r stubs extra dependencies: %s" % (
                        scenario,
                        subject,
                        edera.helpers.render(extra),
                    ))
            for dependency in stubs:
                stack.append((stubs[dependency], dependency))

        result = {test.subject: test}
        stack = []
        handle(test.scenario, test.subject, stack)
        while stack:
            scenario, subject = stack.pop()
            if subject in result:
                if result[subject].scenario == scenario:
                    continue
                raise WorkflowTestificationError(
                    "test %r requires two different stubs for %r: %r and %r" % (
                        test,
                        subject,
                        result[subject].scenario,
                        scenario,
                    ))
            result[subject] = Stub(scenario=scenario, subject=subject)
            handle(scenario, subject, stack)
        return result

    def __generate_color(self, partition):
        return edera.helpers.sha1("\n".join(sorted(test.name for test in partition.items)))[:8]

    def __project(self, workflow, partition, result):
        color = self.__generate_color(partition)
        substitution = {}
        for task in partition.mapping:
            substitute = SuffixingTaskWrapper(partition.mapping[task], " #" + color)
            substitution[task] = substitute
            result.add(substitute)
            result[substitute]["color"] = color
        for task in partition.mapping:
            for parent in workflow[task].parents:
                if parent not in substitution or isinstance(substitution[parent].unwrap(), Test):
                    continue
                result.link(substitution[parent], substitution[task])


class SuffixingTaskWrapper(TaskWrapper):
    """
    A task wrapper that appends a given suffix to the names of the base task and its target.
    """

    def __init__(self, base, suffix):
        """
        Args:
            base (Task) - a base task
            suffix (String) - a suffix to append
        """
        TaskWrapper.__init__(self, base)
        self.__suffix = suffix

    @property
    def name(self):
        return super(SuffixingTaskWrapper, self).name + self.__suffix

    @property
    def target(self):
        if super(SuffixingTaskWrapper, self).target is None:
            return None
        return SuffixingConditionWrapper(super(SuffixingTaskWrapper, self).target, self.__suffix)


class SuffixingConditionWrapper(ConditionWrapper):
    """
    A condition wrapper that appends a given suffix to the name of the base condition.
    """

    def __init__(self, base, suffix):
        """
        Args:
            base (Condition) - a base condition
            suffix (String) - a suffix to append
        """
        ConditionWrapper.__init__(self, base)
        self.__suffix = suffix

    @property
    def expression(self):
        base = super(SuffixingConditionWrapper, self).expression
        if base is None:
            return None
        substitution = {
            atom: SuffixingConditionWrapper(self.from_symbol(atom), self.__suffix).symbol
            for atom in base.atoms()
        }
        return base.xreplace(substitution)

    @property
    def invariants(self):
        for invariant in super(SuffixingConditionWrapper, self).invariants:
            yield SuffixingConditionWrapper(invariant, self.__suffix)

    @property
    def name(self):
        return super(SuffixingConditionWrapper, self).name + self.__suffix
