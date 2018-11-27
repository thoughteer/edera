import contextlib


class CascadeManager(object):
    """
    A context manager that enters/exits all underlying managers one-by-one.
    """

    def __enter__(self):
        self.__current_cascade = self.__cascade(self.managers)
        try:
            self.__current_cascade.__enter__()
        except:
            self.__current_cascade = None
            raise

    def __exit__(self, *args):
        try:
            self.__current_cascade.__exit__(*args)
        finally:
            self.__current_cascade = None

    def __init__(self, managers):
        """
        Args:
            managers (List[ContextManager]) - underlying context managers
        """
        self.managers = managers
        self.__current_cascade = None

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, " - ".join(map(repr, self.managers)))

    @contextlib.contextmanager
    def __cascade(self, managers):

        @contextlib.contextmanager
        def nest(head, tail):
            with head, tail:
                yield

        if not managers:
            yield
            return
        nesting = managers[-1]
        for i in range(2, len(managers) + 1):
            nesting = nest(managers[-i], nesting)
        with nesting:
            yield
