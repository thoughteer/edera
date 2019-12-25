import pytest

import edera.requisites

from edera import Task
from edera.exceptions import RequisiteConformationError
from edera.requisites import Follow
from edera.requisites import SatisfyAll


def test_requisite_conformation_works_correctly():

    class A(Task):
        pass

    assert isinstance(edera.requisites.conform(A()), Follow)
    assert isinstance(edera.requisites.conform([A()]), SatisfyAll)
    assert isinstance(edera.requisites.conform({A(): A()}), SatisfyAll)
    with pytest.raises(RequisiteConformationError):
        edera.requisites.conform(1)
