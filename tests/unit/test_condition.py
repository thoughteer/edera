import pytest
from sympy.logic import boolalg as sympyboolalg

import edera.condition

from edera import Condition


class AlwaysTrue(Condition):

    def check(self):
        return True

    @property
    def name(self):
        return "AlwaysTrue"


class AlwaysFalse(Condition):

    def check(self):
        return False

    @property
    def name(self):
        return "AlwaysFalse"


class SometimesTrue(Condition):

    def check(self):
        return False  # you wish

    @property
    def name(self):
        return "SometimesTrue"


def test_condition_is_abstract():
    with pytest.raises(TypeError):
        Condition()


def test_condition_is_free_of_constraints_by_default():
    true = AlwaysTrue()
    assert not true.invariants
    assert true.expression is None


def test_condition_can_be_recovered_by_symbol():
    true = AlwaysTrue()
    assert true.name in true.symbol.name
    assert true.from_symbol(true.symbol) == true


def test_condition_can_be_negated():
    true = AlwaysTrue()
    negation = ~true
    assert not negation.check()
    assert negation.name == "~AlwaysTrue"
    assert negation.expression == ~true.symbol


def test_conditions_can_be_conjuncted():
    true = AlwaysTrue()
    false = AlwaysFalse()
    conjunction = true & false
    assert not conjunction.check()
    assert conjunction.name == "(AlwaysFalse & AlwaysTrue)"
    assert conjunction.expression == true.symbol & false.symbol


def test_consecutive_conjunctions_fold_into_one():
    true = AlwaysTrue()
    false = AlwaysFalse()
    random = SometimesTrue()
    conjunction = true & (false & random)
    assert not conjunction.check()
    assert conjunction.name == "(AlwaysFalse & AlwaysTrue & SometimesTrue)"
    assert conjunction.expression == sympyboolalg.And(true.symbol, false.symbol, random.symbol)


def test_conditions_can_be_disjuncted():
    true = AlwaysTrue()
    false = AlwaysFalse()
    disjunction = true | false
    assert disjunction.check()
    assert disjunction.name == "(AlwaysFalse | AlwaysTrue)"
    assert disjunction.expression == true.symbol | false.symbol


def test_consecutive_disjunctions_fold_into_one():
    true = AlwaysTrue()
    false = AlwaysFalse()
    random = SometimesTrue()
    disjunction = true | (false | random)
    assert disjunction.check()
    assert disjunction.name == "(AlwaysFalse | AlwaysTrue | SometimesTrue)"
    assert disjunction.expression == sympyboolalg.Or(true.symbol, false.symbol, random.symbol)


def test_conditions_can_be_exclusively_disjuncted():
    true = AlwaysTrue()
    false = AlwaysFalse()
    exclusive_disjunction = true ^ false
    assert exclusive_disjunction.check()
    assert exclusive_disjunction.name == "(AlwaysFalse ^ AlwaysTrue)"
    assert exclusive_disjunction.expression == true.symbol ^ false.symbol


def test_consecutive_exclusive_disjunctions_fold_into_one():
    true = AlwaysTrue()
    false = AlwaysFalse()
    random = SometimesTrue()
    disjunction = true ^ (false ^ random)
    assert disjunction.check()
    assert disjunction.name == "(AlwaysFalse ^ AlwaysTrue ^ SometimesTrue)"
    assert disjunction.expression == sympyboolalg.Xor(true.symbol, false.symbol, random.symbol)


def test_condition_can_imply_another_one():
    true = AlwaysTrue()
    false = AlwaysFalse()
    implication = true >> false
    assert not implication.check()
    assert implication.name == "(AlwaysTrue >> AlwaysFalse)"
    assert implication.expression == true.symbol >> false.symbol
    reverse_implication = true << false
    assert reverse_implication.check()
    assert reverse_implication.name == "(AlwaysFalse >> AlwaysTrue)"
    assert reverse_implication.expression == false.symbol >> true.symbol


def test_conditions_constraint_gets_derived_correctly():

    class TestCondition(Condition):

        def check(self):
            return True

        @property
        def name(self):
            return self.__class__.__name__

    class DatabaseExists(TestCondition):
        pass

    class FirstTableExists(TestCondition):

        @property
        def invariants(self):
            yield self >> DatabaseExists()

    class SecondTableExists(TestCondition):

        @property
        def invariants(self):
            yield self >> DatabaseExists()

    class FirstTableIsEmpty(TestCondition):

        @property
        def invariants(self):
            yield ~self >> FirstTableExists()

    class SecondTableIsEmpty(TestCondition):

        @property
        def invariants(self):
            yield ~self >> SecondTableExists()

    conditions = [
        DatabaseExists(),
        ~FirstTableIsEmpty(),
        ~SecondTableIsEmpty(),
    ]
    derived_constraint = edera.condition.derive_constraint(conditions)
    assert sympyboolalg.is_cnf(derived_constraint)
    expected_constraint = (
        ((~FirstTableIsEmpty()).symbol >> DatabaseExists().symbol)
        & ((~SecondTableIsEmpty()).symbol >> DatabaseExists().symbol)
    )
    equivalence = sympyboolalg.Equivalent(derived_constraint, expected_constraint)
    assert sympyboolalg.simplify_logic(equivalence) is sympyboolalg.true
