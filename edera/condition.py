import abc
import collections
import logging

import sympy
from sympy.logic import boolalg as sympyboolalg

import edera.helpers

from edera.disjointset import DisjointSet
from edera.helpers import memoized
from edera.nameable import Nameable
from edera.routine import deferrable
from edera.routine import routine


class Condition(Nameable):
    """
    An interface for conditions.

    A $Condition object (condition) represents a computable boolean value.
    Conditions are $Nameable, hence hashable and comparable.
    Conditions can be converted to SymPy symbols (and recovered from them).
    Some condition symbols can be expressed in terms of other symbols.
    Conditions can also provide invariants (other conditions that always hold true).

    You can use various boolean operations (~, &, |, ^, >>, <<) to combine conditions.

    Conditions are primarily used to declare task targets.

    Attributes:
        expression (Optional[sympyboolalg.Boolean]) - a symbolic expression which is considered
                to be equivalent to this condition's symbol
            Default is $None.
        invariants (Iterable[Condition]) - a set of conditions that always hold true
            The equivalence to the $expression is also an invariant, but there is no need
            to specify it explicitly.
            Default is an empty list.
        symbol (sympy.Symbol) - the corresponding symbol
            There is no need to override it.
            Added mainly for internal purposes.

    Examples:
        Here is the classical "file exists" condition:

            >>> import os
            >>> import os.path
            >>> class MyFileExists(Condition):
            >>>     def check(self):
            >>>         return os.path.exists("my.file")
            >>>     @property
            >>>     def name(self):
            >>>         return "MyFileExists"
            >>> class MyFileIsNotEmpty(Condition):
            >>>     def check(self):
            >>>         return os.path.exists("my.file") and os.stat("my.file").st_size > 0
            >>>     @property
            >>>     def invariants(self):
            >>>         yield self >> MyFileExists()  # "is not empty" implies "exists"
            >>>     @property
            >>>     def name(self):
            >>>         return "MyFileIsNotEmpty"
            >>> MyFileExists().check()
            True
            >>> MyFileIsNotEmpty().check()
            False
            >>> (~MyFileIsNotEmpty()).check()
            True
            >>> (MyFileExists() & MyFileIsNotEmpty()).check()
            False
            >>> (MyFileExists() | MyFileIsNotEmpty()).check()
            True
            >>> (MyFileExists() >> MyFileIsNotEmpty()).check()
            False

    See also:
        $Parameterizable
        $Task.target
    """

    __instances = {}

    def __and__(self, other):
        if isinstance(other, ConditionConjunction):
            return NotImplemented
        return ConditionConjunction((self, other))

    def __invert__(self):
        return ConditionNegation(self)

    def __lshift__(self, other):
        return ConditionImplication(other, self)

    def __or__(self, other):
        if isinstance(other, ConditionDisjunction):
            return NotImplemented
        return ConditionDisjunction((self, other))

    def __rshift__(self, other):
        return ConditionImplication(self, other)

    def __xor__(self, other):
        if isinstance(other, ConditionExclusiveDisjunction):
            return NotImplemented
        return ConditionExclusiveDisjunction((self, other))

    @abc.abstractmethod
    def check(self):
        """
        Compute and return the boolean value of the condition.

        If uncertain, raise an exception instead.

        Returns:
            Boolean - the value of the condition
        """

    @property
    def expression(self):
        return None

    @classmethod
    def from_symbol(cls, symbol):
        """
        Recover a condition from its symbol.

        The symbol must be obtained via the $Condition.symbol property.

        Args:
            symbol (sympy.Symbol) - a condition symbol

        Returns:
            Condition

        Raises:
            AssertionError if $symbol does not represent a condition
        """
        assert symbol.name in cls.__instances
        return cls.__instances[symbol.name]

    @property
    def invariants(self):
        return []

    @property
    def name(self):
        return self.__class__.__name__

    @property
    @memoized
    def symbol(self):
        symbol_name = "${%s}" % self.name
        self.__instances[symbol_name] = self
        return sympy.Symbol(symbol_name)

    def unwrap(self):
        """
        Unwrap the condition if it has been wrapped.

        Returns:
            Condition
        """
        return self


class ConditionWrapper(Condition):
    """
    A condition wrapper.

    Delegates all its method calls to the base condition object.
    Allows you to override (wrap) any subset of condition methods/properties.
    """

    def __init__(self, base):
        """
        Args:
            base (Condition) - a base condition
        """
        self.__base = base

    @property
    def check(self):
        return self.__base.check

    @property
    def expression(self):
        return self.__base.expression

    @property
    def invariants(self):
        return self.__base.invariants

    @property
    def name(self):
        return self.__base.name

    def unwrap(self):
        return self.__base


class ConditionNegation(Condition):
    """
    The negation of a condition.
    """

    def __init__(self, condition):
        """
        Args:
            condition (Condition) - a condition to negate
        """
        self.__condition = condition

    @routine
    def check(self):
        base = yield deferrable(self.__condition.check).defer()
        yield not base

    @property
    def expression(self):
        return ~self.__condition.symbol

    @property
    def name(self):
        return "~%s" % self.__condition.name


class ConditionConjunction(Condition):
    """
    The conjunction of conditions.
    """

    def __and__(self, other):
        if isinstance(other, ConditionConjunction):
            return ConditionConjunction(self.__conditions + other.__conditions)
        return ConditionConjunction(self.__conditions + (other,))

    def __init__(self, conditions):
        """
        Args:
            conditions (Iterable[Condition]) - conditions to conjunct
        """
        self.__conditions = tuple(conditions)

    def __rand__(self, other):
        return ConditionConjunction((other,) + self.__conditions)

    @routine
    def check(self):
        for condition in self.__conditions:
            base = yield deferrable(condition.check).defer()
            if not base:
                yield False
                return
        yield True

    @property
    def expression(self):
        return sympyboolalg.And(*(condition.symbol for condition in self.__conditions))

    @property
    def name(self):
        return "(%s)" % " & ".join(sorted(condition.name for condition in self.__conditions))


class ConditionDisjunction(Condition):
    """
    The disjunction of conditions.
    """

    def __init__(self, conditions):
        """
        Args:
            conditions (Iterable[Condition]) - conditions to disjunct
        """
        self.__conditions = tuple(conditions)

    def __or__(self, other):
        if isinstance(other, ConditionDisjunction):
            return ConditionDisjunction(self.__conditions + other.__conditions)
        return ConditionDisjunction(self.__conditions + (other,))

    def __ror__(self, other):
        return ConditionDisjunction((other,) + self.__conditions)

    @routine
    def check(self):
        for condition in self.__conditions:
            base = yield deferrable(condition.check).defer()
            if base:
                yield True
                return
        yield False

    @property
    def expression(self):
        return sympyboolalg.Or(*(condition.symbol for condition in self.__conditions))

    @property
    def name(self):
        return "(%s)" % " | ".join(sorted(condition.name for condition in self.__conditions))


class ConditionExclusiveDisjunction(Condition):
    """
    The exclusive disjunction of conditions.
    """

    def __init__(self, conditions):
        """
        Args:
            conditions (Iterable[Condition]) - conditions to exclusively disjunct
        """
        self.__conditions = tuple(conditions)

    def __rxor__(self, other):
        return ConditionExclusiveDisjunction((other,) + self.__conditions)

    def __xor__(self, other):
        if isinstance(other, ConditionExclusiveDisjunction):
            return ConditionExclusiveDisjunction(self.__conditions + other.__conditions)
        return ConditionExclusiveDisjunction(self.__conditions + (other,))

    @routine
    def check(self):
        result = False
        for condition in self.__conditions:
            base = yield deferrable(condition.check).defer()
            result ^= base
        yield result

    @property
    def expression(self):
        return sympyboolalg.Xor(*(condition.symbol for condition in self.__conditions))

    @property
    def name(self):
        return "(%s)" % " ^ ".join(sorted(condition.name for condition in self.__conditions))


class ConditionImplication(Condition):
    """
    The implication between two conditions.
    """

    def __init__(self, cause, effect):
        """
        Args:
            cause (Condition) - a "cause" condition
            effect (Condition) - an "effect" condition

        Defines the implication ("cause" => "effect").
        """
        self.__cause = cause
        self.__effect = effect

    @routine
    def check(self):
        effect = yield deferrable(self.__effect.check).defer()
        if effect:
            yield True
            return
        cause = yield deferrable(self.__cause.check).defer()
        yield not cause

    @property
    def expression(self):
        return self.__cause.symbol >> self.__effect.symbol

    @property
    def name(self):
        return "(%s >> %s)" % (self.__cause.name, self.__effect.name)


def derive_constraint(conditions):
    """
    Derive a symbolic expression that binds the conditions.

    It is mainly used to analyze the consistency of a workflow, i.e. whether task targets
    fundamentally contradict each other, preventing the workflow from reaching the fully complete
    (or fully incomplete) state, thus complicating workflow optimization.

    Args:
        conditions (Iterable[Condition]) - conditions to derive a constraint for

    Returns:
        sympyboolalg.Boolean - the constraint expression

    See also:
        $WorkflowNormalizer
    """
    conditions = set(conditions)
    logging.getLogger(__name__).debug(
        "Deriving a constraint for the set of conditions: %s", edera.helpers.render(conditions))
    return sympyboolalg.And(*_derive_active_constraints(conditions))


def _derive_active_constraints(conditions):
    if not conditions:
        return
    global_constraints = list(_derive_global_constraints(conditions))
    constraint_groups = _group_by_atoms(global_constraints)
    logging.getLogger(__name__).debug("Derived %d constraint groups", len(constraint_groups))
    active_atoms = {condition.symbol for condition in conditions}
    logging.getLogger(__name__).debug("Reducing to %d active atoms", len(active_atoms))
    for constraint_group in constraint_groups:
        for expression in _reduce_expressions(constraint_group, active_atoms):
            yield expression


def _derive_global_constraints(conditions):
    stack = list(conditions)
    collector = {condition.symbol for condition in conditions}
    while stack:
        condition = stack.pop()
        for constraint in _derive_local_constraints(condition):
            yield constraint
            unknowns = constraint.atoms() - collector
            stack.extend(map(Condition.from_symbol, unknowns))
            collector.update(unknowns)


def _derive_local_constraints(condition):
    if condition.expression is not None:
        yield sympyboolalg.Equivalent(condition.symbol, condition.expression)
    for invariant in condition.invariants:
        yield invariant.symbol


def _group_by_atoms(expressions):
    expression_groups = DisjointSet(len(expressions))
    atom_groups = {}
    for index, expression in enumerate(expressions):
        for atom in expression.atoms():
            if atom in atom_groups:
                expression_groups.merge(index, atom_groups[atom])
            else:
                atom_groups[atom] = index
    grouped_expressions = collections.defaultdict(list)
    for index, expression in enumerate(expressions):
        grouped_expressions[expression_groups.find(index)].append(expression)
    return grouped_expressions.values()


def _reduce_expressions(expressions, atoms):
    expressions = [
        sympyboolalg.simplify_logic(expression, form="cnf")
        for expression in expressions
    ]
    logging.getLogger(__name__).debug("Reducing: %s", edera.helpers.render(expressions))
    inactive_atoms = set.union(*(expression.atoms() for expression in expressions)) - atoms
    counters = collections.Counter()
    for atom in inactive_atoms:
        for expression in expressions:
            if atom in expression.atoms():
                counters[atom] += len(expression.atoms())
    for _, _, atom in sorted((counters[atom], str(atom), atom) for atom in counters):
        focused = []
        index = 0
        for expression in expressions:
            if atom in expression.atoms():
                focused.append(expression)
            else:
                expressions[index] = expression
                index += 1
        del expressions[index:]
        focus = sympyboolalg.And(*focused)
        focus = focus.xreplace({atom: False}) | focus.xreplace({atom: True})
        focus = sympyboolalg.simplify_logic(focus, form="cnf")
        expressions.append(focus)
    logging.getLogger(__name__).debug("Reduced to: %s", edera.helpers.render(expressions))
    for expression in expressions:
        yield expression
