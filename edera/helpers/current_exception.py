import sys

import six


class CurrentException(object):
    """
    A "frozen-traceback" exception wrapper that improves exception handling.

    Examples:
        Imagine you need to do something before re-raising an exception:

            >>> try:
            >>>     1 / 0
            >>> except ZeroDivisionError as error:
            >>>     print("WTF?!")
            >>>     raise error

        In this case, the original traceback will be lost and you'll have to find the `1 / 0` line
        all by yourself.
        You could, however, re-raise the last exception using `raise` (no arguments),
        but this approach would fail, for instance, in the following case:

            >>> try:
            >>>     1 / 0
            >>> except ZeroDivisionError as error:
            >>>     try:
            >>>         {"one": 1}["two"]
            >>>     except KeyError:
            >>>         pass
            >>>     raise

        That's where $CurrentException comes in handy:

            >>> try:
            >>>     1 / 0
            >>> except ZeroDivisionError:
            >>>     error = CurrentException()
            >>>     print("WTF?!")
            >>>     try:
            >>>         {"one": 1}["two"]
            >>>     except KeyError:
            >>>         pass
            >>>     error.reraise()
    """

    def __init__(self):
        self.__info = sys.exc_info()

    def reraise(self):
        """
        Re-raise the exception with the original traceback.
        """
        six.reraise(*self.__info)
