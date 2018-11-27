from edera.parameterizable import Parameter
from edera.parameterizable import Parameterizable
from edera.qualifiers import Integer
from edera.qualifiers import TimeDelta


class DaemonSchedule(Parameterizable):
    """
    A daemon schedule.

    The daemon will re-build the workflow at most once per $building_delay and execute it in
    $executor_count workers at most once per $execution_delay.
    """

    building_delay = Parameter(TimeDelta, default="PT1M")
    execution_delay = Parameter(TimeDelta, default="PT5S")
    executor_count = Parameter(Integer, default=1)
