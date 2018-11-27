from edera.helpers.factory import Factory


class Lazy(Factory[object]):
    """
    A wrapper that delays object instantiation.

    You pass the class of the object as a cargo (see $Factory for details).
    The object will be instantiated on the first access to the $instance attribute.
    After that, the object will not be re-instantiated.
    To do so, you have to destroy it explicitly.

    This wrapper helps to prevent external APIs from performing unwanted activities "immediately",
    like establishing connections or spawning background threads.

    Attributes:
        *args, **kwargs - arguments to pass to the constructor
        instance (Any) - the instantiated object

    Examples:
        >>> import threading
        >>> import time
        >>> class DirtyObject(object):
        >>>     def __init__(self):
        >>>         pooper = threading.Thread(target=self.poop)
        >>>         pooper.daemon = True
        >>>         pooper.start()
        >>>     def poop(self):
        >>>         while True:
        >>>             print("Pooping")
        >>>             time.sleep(1)
        >>> DirtyObject()  # spawns a pooper
        >>> lazy = Lazy[DirtyObject]()  # does not spawn a pooper
        >>> lazy.instance  # here we go
        >>> lazy.destroy()  # still keeps pooping
        >>> lazy.instance  # now a second pooper is spawned

    See also:
        $Factory
    """

    def __init__(self, *args, **kwargs):
        """
        Args:
            *args, **kwargs - arguments to pass to the constructor
        """
        self.args = args
        self.kwargs = kwargs
        self.__instance = None

    def destroy(self):
        """
        Destroy internal references to the instantiated object.

        This allows you to re-instantiate the object.
        """
        self.__instance = None

    @property
    def instance(self):
        if self.__instance is None:
            self.__instance = self.cargo(*self.args, **self.kwargs)
        return self.__instance
