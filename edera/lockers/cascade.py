from edera.locker import Locker
from edera.managers import CascadeManager


class CascadeLocker(Locker):
    """
    A hierarchical locker that successively acquires a number of sub-locks.

    Attributes:
        sublockers (Tuple[Locker]) - the sub-lockers
    """

    def __init__(self, *sublockers):
        """
        Args:
            sublockers (Tuple[Locker]) - sub-lockers used to acquire sub-locks
        """
        self.sublockers = sublockers

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, " - ".join(map(repr, self.sublockers)))

    def lock(self, key, callback=None):
        sublocks = [sublocker.lock(key, callback=callback) for sublocker in self.sublockers]
        return CascadeManager(sublocks)
