import logging

import pytest


@pytest.fixture
def debugger(caplog):
    caplog.set_level(logging.DEBUG)
