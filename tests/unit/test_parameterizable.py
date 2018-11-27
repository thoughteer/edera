import pytest

from edera import Nameable
from edera import Parameter
from edera import Parameterizable
from edera import parameter
from edera.exceptions import UndefinedParameterError
from edera.exceptions import UnknownParameterError


class BaseThing(Parameterizable):

    required_parameter = Parameter()
    optional_parameter = Parameter(default="default")

    @parameter
    def evaluated_parameter(self):
        return "based on " + self.required_parameter


class DerivedThing(BaseThing):

    @parameter
    def required_parameter(self):
        return "no longer required"

    @property
    def optional_parameter(self):
        return "hidden"


def test_parameterizable_accepts_only_known_parameters():
    with pytest.raises(UnknownParameterError):
        BaseThing(unknown_parameter=True)


def test_parameter_with_no_default_value_requires_specification():
    with pytest.raises(UndefinedParameterError):
        BaseThing()


def test_default_parameter_value_can_be_evaluated():
    base_thing = BaseThing(required_parameter="x")
    assert base_thing.required_parameter == "x"
    assert base_thing.optional_parameter == "default"
    assert base_thing.evaluated_parameter == "based on x"


def test_default_parameter_value_can_be_overridden():
    base_thing = BaseThing(required_parameter="x", optional_parameter="y", evaluated_parameter="z")
    assert base_thing.required_parameter == "x"
    assert base_thing.optional_parameter == "y"
    assert base_thing.evaluated_parameter == "z"


def test_derived_class_can_shadow_inherited_parameters():
    derived_thing = DerivedThing()
    assert derived_thing.required_parameter == "no longer required"
    assert derived_thing.optional_parameter == "hidden"
    assert derived_thing.evaluated_parameter == "based on no longer required"
    derived_thing = DerivedThing(required_parameter="x")
    assert derived_thing.required_parameter == "x"
    assert derived_thing.evaluated_parameter == "based on x"
    derived_thing = DerivedThing(required_parameter="x", evaluated_parameter="y")
    assert derived_thing.required_parameter == "x"
    assert derived_thing.evaluated_parameter == "y"
    with pytest.raises(UnknownParameterError):
        DerivedThing(optional_parameter="z")


def test_parameter_attribute_has_distinguishable_class():
    assert isinstance(BaseThing.evaluated_parameter, Parameter)


def test_parameterizable_has_stable_name():
    assert DerivedThing().name == DerivedThing().name


def test_parameterizable_name_depends_on_class():
    derived_thing = DerivedThing()
    similar_base_thing = BaseThing(
        required_parameter="no longer required", optional_parameter="hidden")
    assert similar_base_thing.name != derived_thing.name


def test_parameterizable_name_depends_on_parameter_values():
    default_derived_thing = DerivedThing()
    custom_derived_thing = DerivedThing(required_parameter="custom")
    assert custom_derived_thing.name != default_derived_thing.name


def test_parameterization_works_well_with_multiple_inheritance():

    class AbstractNameableThing(Nameable):
        pass

    class ConcreteNameableThing(Parameterizable, AbstractNameableThing):

        @parameter
        def some(self):
            return "some"

    assert ConcreteNameableThing().name  # should not fail with TypeError
    assert ConcreteNameableThing().some == "some"
    assert ConcreteNameableThing(some="any").some == "any"


def test_parameterizable_provides_access_to_all_parameter_instances():
    thing = BaseThing(required_parameter="0", optional_parameter="1", evaluated_parameter="2")
    assert thing.parameters["required_parameter"].value == "0"
    assert repr(thing.parameters["required_parameter"]) == "'0'"
    assert thing.parameters["optional_parameter"].value == "1"
    assert repr(thing.parameters["optional_parameter"]) == "'1'"
    assert thing.parameters["evaluated_parameter"].value == "2"
    assert repr(thing.parameters["evaluated_parameter"]) == "'2'"
