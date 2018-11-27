"""
This module implements various classes for workflow auto-testing.
"""

from .scenarios import DefaultScenario
from .scenarios import Scenario
from .scenarios import ScenarioWithProvidedStubs
from .selectors import AllTestSelector
from .selectors import RegexTestSelector
from .selectors import TestSelector
from .tasks import Stub
from .tasks import Test
from .tasks import TestableTask
