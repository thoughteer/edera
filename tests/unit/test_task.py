from edera import Task
from edera import TaskWrapper
from edera.helpers import Phony


def test_default_task_is_non_abstract():
    task = Task()
    assert task.execute is Phony
    assert task.name == "Task"
    assert task.requisite is None
    assert task.target is None
    assert task.unwrap() is task


def test_task_wrapper_behaves_as_expected():
    task = Task()
    wrapper = TaskWrapper(task)
    assert wrapper.execute is Phony
    assert wrapper.name == "Task"
    assert wrapper.requisite is None
    assert wrapper.target is None
    assert wrapper.unwrap() is task
