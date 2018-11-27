import logging

import edera.helpers

from edera.condition import ConditionWrapper
from edera.exceptions import StorageOperationError
from edera.routine import deferrable
from edera.routine import routine
from edera.workflow.processor import WorkflowProcessor
from edera.workflow.processors.workflow_normalizer import TargetOverridingTaskWrapper


class TargetCacher(WorkflowProcessor):
    """
    A workflow processor that makes tasks cache targets.

    Makes each task examine the cache before checking the original target.
    It also makes each task register its target in the cache once the target becomes $True.

    You can stack up multiple cachers for better performance:

        >>> # this is the preferred order
        >>> TargetCacher(remote_storage).process(workflow)
        >>> TargetCacher(local_storage).process(workflow)

    Attributes:
        cache (Storage) - the cache used

    See also:
        $WorkflowNormalizer

    WARNING!
        This optimization may not work as expected with unnormalized workflows.
        Consider applying $WorkflowNormalizer first.
    """

    def __init__(self, cache):
        """
        Args:
            cache (Storage) - a cache to use
        """
        self.cache = cache

    def process(self, workflow):
        for task in workflow:
            if task.target is None:
                continue
            target = CachingConditionWrapper(task.target, self.cache)
            workflow.replace(TargetOverridingTaskWrapper(task, target))


class CachingConditionWrapper(ConditionWrapper):
    """
    A condition wrapper that caches itself in a storage.

    Attributes:
        cache (Storage) - the cache used
    """

    def __init__(self, base, cache):
        """
        Args:
            base (Condition) - a base condition
            cache (Storage) - a cache to use
        """
        ConditionWrapper.__init__(self, base)
        self.cache = cache

    @routine
    def check(self):
        cached = True
        try:
            logging.getLogger(__name__).debug("Looking up for %r in cache", self)
            if self.cache.get(edera.helpers.sha1(self.name), limit=1):
                logging.getLogger(__name__).debug("Found in cache")
                yield True
                return
            cached = False
        except StorageOperationError:
            pass  # not sure if really not cached
        result = yield deferrable(super(CachingConditionWrapper, self).check).defer()
        if result and not cached:
            try:
                logging.getLogger(__name__).debug("Caching %r", self)
                self.cache.put(edera.helpers.sha1(self.name), "!")
                logging.getLogger(__name__).debug("Stored in cache")
            except StorageOperationError:
                pass  # whatever
        yield result
