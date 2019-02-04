import abc

import six

from edera.daemon.schedule import DaemonSchedule


@six.add_metaclass(abc.ABCMeta)
class DaemonModule(object):
    """
    A daemon module.

    Incapsulates information on "what" and "how to" execute.

    Attributes:
        scheduling (Mapping[Optional[String], DaemonSchedule]) - schedules for different tags
            Here $None means "any tag".
    """

    @property
    def scheduling(self):
        return {None: DaemonSchedule()}

    @abc.abstractmethod
    def seed(self, now):
        """
        Generate a root task for the workflow at $now.

        Args:
            now (DateTime) - an "aware" timestamp

        Returns:
            Task
        """


class StaticDaemonModule(DaemonModule):
    """
    A daemon module with a static seeder.

    Uses the same root task at all times.

    Attributes:
        root (Task) - the root task
    """

    @abc.abstractproperty
    def root(self):
        pass

    def seed(self, now):
        return self.root
