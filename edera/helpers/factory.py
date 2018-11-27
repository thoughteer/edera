import six


class FactoryMeta(type):

    def __getitem__(cls, cargo):
        """
        Args:
            cargo (Any) - a cargo to parameterize the class with

        Returns:
            Type - the same class as $cls, but with the cargo
        """
        if not hasattr(cls, "cargo"):
            body = dict(cls.__dict__)
            body["cargo"] = cargo
            return type.__new__(cls.__class__, cls.__name__, cls.__bases__, body)
        body = dict(cls.cargo.__dict__)
        body.update(cls.__dict__)
        body["cargo"] = cargo
        result = cls.cargo.__class__.__new__(cls.cargo.__class__, cls.__name__, (cls.cargo,), body)
        return result


@six.add_metaclass(FactoryMeta)
class Factory(object):
    """
    A factory that allows to create statically parameterized subclasses of a given class.

    The base class is passed to the factory class in square brackets.
    The body of each subclass is overridden by the body of the factory class itself.
    The parameters are stored in the $cargo attribute of the subclass.

    Examples:
        >>> import abc
        >>> import six
        >>> @six.add_metaclass(abc.ABCMeta)
        >>> class Computable(object):
        >>>     @abc.abstractmethod
        >>>     def compute(self):
        >>>         pass
        >>> class TruncatedString(Factory[Computable]):
        >>>     def __init__(self, string):
        >>>         self.string = string
        >>>     def compute(self):  # this will override the abstract base method
        >>>         return self.string[:self.cargo]
        >>> TruncatedString[4]("hello").compute()
        'hell'
    """
