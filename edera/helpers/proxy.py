import inspect


SPECIAL_METHODS = {
    "__abs__", "__add__", "__and__", "__call__", "__cmp__", "__coerce__", "__contains__",
    "__delattr__", "__delitem__", "__delslice__", "__div__", "__divmod__", "__eq__", "__float__",
    "__floordiv__", "__ge__", "__getattribute__", "__getitem__", "__getslice__", "__gt__",
    "__hash__", "__hex__", "__int__", "__invert__", "__iter__", "__le__", "__len__", "__long__",
    "__lshift__", "__lt__", "__mod__", "__mul__", "__ne__", "__next__", "__neg__", "__nonzero__",
    "__oct__", "__or__", "__pos__", "__pow__", "__radd__", "__rand__", "__rdiv__", "__rdivmod__",
    "__reduce__", "__reduce_ex__", "__repr__", "__reversed__", "__rfloorfiv__", "__rlshift__",
    "__rmod__", "__rmul__", "__ror__", "__rpow__", "__rrshift__", "__rshift__", "__rsub__",
    "__rtruediv__", "__rxor__", "__setattr__", "__setitem__", "__setslice__", "__str__",
    "__sub__", "__truediv__", "__xor__", "next",
}


class Proxy(object):
    """
    A lazy object proxy.

    It delays subject instantiation till the moment of its first use, stores the instance in a given
    box, and then delegates attribute access to this instance.
    It takes care of proxying special methods as well.

    Examples:
        >>> box = SimpleBox()
        >>> proxy = Proxy(box, list)  # this will behave exactly like a list
        >>> box.get() is None
        True
        >>> proxy
        []
        >>> proxy.__class__
        list
        >>> box.get()
        []
        >>> proxy.extend([1, "b"])
        >>> proxy
        [1, 'b']
        >>> len(proxy)
        2
        >>> proxy[1]
        'b'
        >>> proxy[1] = 2
        >>> proxy
        [1, 2]
    """

    def __new__(cls, instance_holder, subject_class, *args, **kwargs):
        """
        Args:
            instance_holder (Box) - a box to store the subject in
            subject_class (Type) - a class to proxy
            *args, **kwargs - arguments to pass to the subject constructor
        """

        def proxy(method_name):

            def instantiate():
                return subject_class(*args, **kwargs)

            def method(self, *args, **kwargs):
                subject = instance_holder.get()
                if subject is None:
                    subject = instantiate()
                    instance_holder.put(subject)
                return object.__getattribute__(subject, method_name)(*args, **kwargs)

            return method

        body = dict(object.__dict__)
        special_subject_class_methods = {
            name
            for name, _ in inspect.getmembers(subject_class)
            if name in SPECIAL_METHODS
        }
        for method_name in special_subject_class_methods:
            body[method_name] = proxy(method_name)
        return type.__new__(type, subject_class.__name__, subject_class.__bases__, body)()
