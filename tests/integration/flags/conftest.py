import pytest

from edera.flags import InterProcessFlag
from edera.flags import InterThreadFlag


@pytest.fixture
def interprocess_flag():
    return InterProcessFlag()


@pytest.fixture
def interthread_flag():
    return InterThreadFlag()


@pytest.fixture(params=["interprocess_flag", "interthread_flag"])
def flag(request):
    return request.getfixturevalue(request.param)
