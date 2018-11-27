import inspect

import six

from edera.exceptions import UndefinedParameterError
from edera.exceptions import UnknownParameterError
from edera.nameable import Nameable
from edera.qualifiers import String


class Parameterizable(Nameable):
    """
    An object that is determined completely by its class and parameters.

    A parameterizable object automatically generates its $name property and its $__init__ method.
    It finds $Parameter objects among its attributes, evaluates them in the $__init__ method, and
    then uses them to construct a unique name.

    Attributes:
        parameters (Mapping[String, ParameterInstance]) - the parameter instances (by name)

    Examples:
        Here is an example of a class that aims to represent 3D points:

            >>> class Point(Parameterizable):
            >>>     x = Parameter(Integer)
            >>>     @parameter(Integer)
            >>>     def y(self):
            >>>         return x**2  # will be auto-evaluated if not specified
            >>>     z = Parameter(Integer, default=8)  # will use static default value
            >>> Point()  # will raise UndefinedParameterError
            >>> Point(x="2")  # will raise ValueQualificationError
            >>> Point(x=2)
            Point(x=2, y=4, z=8)
            >>> Point(x=2, y=5)
            Point(x=2, y=5, z=8)
            >>> Point(x=2, y=5, z=9)
            Point(x=2, y=5, z=9)
            >>> Point(x=2, y=5, z=9, o=0)  # will raise UnknownParameterError

    See also:
        $parameter
        $Parameter
    """

    def __hash__(self):
        return self.__hash

    def __init__(self, **kwargs):
        """
        Args:
            **kwargs - parameter values to be set manually

        Raises:
            UnknownParameterError if you passed an unknown parameter
            UndefinedParameterError if you didn't pass a required parameter
            ValueQualificationError if you passed an invalid value for a parameter
        """
        self.__class__.introspect()
        self.parameters = {}
        for name in kwargs:
            if name not in self.__class__.__parameters__:
                raise UnknownParameterError(name)
            self.parameters[name] = self.__class__.__parameters__[name].instantiate(kwargs[name])
        for name in self.__class__.__parameters__:
            getattr(self, name)
        arguments = [
            "%s=%r" % (name, instance)
            for name, instance in sorted(self.parameters.items())
        ]
        self.__name = "%s(%s)" % (self.__class__.__name__, ", ".join(arguments))
        self.__hash = hash(self.__name)

    @classmethod
    def introspect(cls):
        if hasattr(cls, "__powner__") and cls.__powner__ is cls:
            return
        cls.__parameters__ = {
            name: attribute
            for name, attribute in inspect.getmembers(cls)
            if isinstance(attribute, Parameter)
        }
        for name, attribute in six.iteritems(cls.__parameters__):
            attribute.name = name
        cls.__powner__ = cls

    @property
    def name(self):
        return self.__name


class NoDefault(object):
    """
    A singleton that represents the absence of the default parameter value.
    """


class Parameter(property):
    """
    A parameter object.

    Works as an overridable, type-safe property.

    Attributes:
        name (Optional[String]) - the name of the parameter

    See also:
        $parameter
    """

    def __init__(self, qualifier=String, evaluator=None, default=NoDefault):
        """
        Args:
            qualifier (Qualifier) - a qualifier
                Used for type control and value unification.
                Default is $String.
            evaluator (Optional[Callable[[Any], Any]]) - a default value evaluator
                Default is $None - no default value.
            default (Any) - an optional static default value
                Default corresponds to an unspecified value.
                The $evaluator always takes precedence over $default if provided.

        It is safe to assume that the $qualifier argument always goes first.

        See also:
            $Qualifier
        """
        property.__init__(self, self.__evaluate)
        self.name = None
        self.__qualifier = qualifier
        self.__evaluator = evaluator or self.__evaluate_default
        self.__default = default

    def instantiate(self, value):
        """
        Try to qualify the given value as a value for the parameter to get a $ParameterInstance.

        Returns:
            ParameterInstance

        Raises:
            ValueQualificationError if the qualification failed
        """
        return ParameterInstance(*self.__qualifier.qualify(value))

    def __evaluate(self, owner):
        if self.name not in owner.parameters:
            value = self.__evaluator(owner)
            owner.parameters[self.name] = self.instantiate(value)
        return owner.parameters[self.name].value

    def __evaluate_default(self, owner):
        if self.__default is NoDefault:
            raise UndefinedParameterError(self.name)
        return self.__default


class ParameterInstance(object):
    """
    A specific parameter value holder for a specific owner.

    Attributes:
        value (Any)
    """

    def __init__(self, value, representation):
        """
        Args:
            value (Any) - a value to hold
            representation (String) - a representation to use in $__repr__
        """
        self.__value = value
        self.__representation = representation

    def __repr__(self):
        return self.__representation

    @property
    def value(self):
        return self.__value


def parameter(evaluator=None, qualifier=String):
    """
    Create a $Parameter object by decorating the evaluator.

    Args:
        evaluator (Optional[Callable[[Any], Any]]) - a default value evaluator
            This is the decorated method.
        qualifier (Qualifier) - a qualifier
            Default is $String.

    It is safe to assume that the $evaluator argument always goes first.

    This decorator can be called in two ways (with and without a custom qualifier):

        >>> @parameter  # $String will be used by default
        >>> def p(self):
        >>>     return "0"
        >>> @parameter(qualifier=Integer)
        >>> def p(self):
        >>>     return 0

    See also:
        $Parameter
        $Qualifier
    """

    def decorate(evaluator):
        return Parameter(qualifier, evaluator=evaluator)

    return decorate if evaluator is None else decorate(evaluator)
