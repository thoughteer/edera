from edera import Condition
from edera import Task
from edera.exceptions import StorageOperationError
from edera.storages import InMemoryStorage
from edera.workflow import WorkflowBuilder
from edera.workflow.processors import TargetCacher


def test_target_cacher_checks_target_only_once():

    class C(Condition):

        def check(self):
            counter[0] += 1
            return True

    class T(Task):

        target = C()

    counter = [0]
    workflow = WorkflowBuilder().build(T())
    cache = InMemoryStorage()
    TargetCacher(cache).process(workflow)
    assert workflow[T()].item.target.check()
    assert counter[0] == 1
    assert len(cache.gather()) == 1
    assert workflow[T()].item.target.check()
    assert counter[0] == 1


def test_target_cacher_skips_false_targets():

    class C(Condition):

        def check(self):
            return False

    class T(Task):

        target = C()

    workflow = WorkflowBuilder().build(T())
    cache = InMemoryStorage()
    TargetCacher(cache).process(workflow)
    assert not workflow[T()].item.target.check()
    assert not cache.gather()


def test_target_cacher_prevents_flooding():

    class WriteOnlyStorage(InMemoryStorage):

        def get(self, key, since=None, limit=None):
            raise StorageOperationError("no")

    class C(Condition):

        def check(self):
            counter[0] += 1
            return True

    class T(Task):

        target = C()

    counter = [0]
    workflow = WorkflowBuilder().build(T())
    cache = WriteOnlyStorage()
    TargetCacher(cache).process(workflow)
    assert workflow[T()].item.target.check()
    assert counter[0] == 1
    assert not cache.gather()
    assert workflow[T()].item.target.check()
    assert counter[0] == 2
    assert not cache.gather()


def test_target_cacher_ignores_errors():

    class ReadOnlyStorage(InMemoryStorage):

        def put(self, key, value):
            raise StorageOperationError("no")

    class C(Condition):

        def check(self):
            return True

    class T(Task):

        target = C()

    workflow = WorkflowBuilder().build(T())
    cache = ReadOnlyStorage()
    TargetCacher(cache).process(workflow)
    assert workflow[T()].item.target.check()
    assert not cache.gather()