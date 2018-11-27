class Phony(object):
    """
    A class that can be used as a callable singleton.

    Does nothing and returns $None when called:

        >>> Phony(1, 2, blah="blah") is None
        True

    See also:
        $phony
    """

    def __new__(cls, *args, **kwargs):
        pass


def phony(function):
    """
    A useful decorator that marks a function/method "phony".

    Args:
        function (Any) - any object, actually

    The result of the decoration is always $Phony:

        >>> @phony
        >>> def square(x):
        >>>     return x**2
        >>> square(2) is None
        True
        >>> square is Phony
        True
    """
    return Phony
