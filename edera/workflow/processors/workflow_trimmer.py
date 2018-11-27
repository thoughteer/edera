import binascii
import logging

import six

from edera.graph import Graph
from edera.linearizers import DFSLinearizer
from edera.routine import deferrable
from edera.routine import routine
from edera.workflow.processor import WorkflowProcessor


class WorkflowTrimmer(WorkflowProcessor):
    """
    A workflow optimizer.

    Trims the task graph using task targets.
    It assumes that if a task is complete, then all its ancestors are also complete.
    Vice versa, if a task is incomplete, then all its descendants are also incomplete.

    See also:
        $WorkflowNormalizer

    WARNING!
        The trick works only for normalized workflows.
        Consider applying $WorkflowNormalizer first.
    """

    @routine
    def process(self, workflow):
        logging.getLogger(__name__).debug("Tasks before trimming: %d", len(workflow))
        tasks = DFSLinearizer().linearize(workflow)
        hashes = [binascii.crc32(task.name.encode("ASCII")) for task in tasks]
        indices = {task: index for index, task in enumerate(tasks)}
        linearization = list(range(len(indices)))
        candidates = Graph()
        for index in linearization:
            candidates.add(index)
            for parent in workflow[tasks[index]].parents:
                candidates.link(indices[parent], index)
        while True:
            yield
            for index in linearization:
                parents = candidates[index].parents
                if not parents:
                    candidates[index]["AS"] = None
                    candidates[index]["AC"] = 0
                    continue
                counters = {}
                for parent in parents:
                    signature = candidates[parent]["AS"]
                    if signature is None:
                        continue
                    count = candidates[parent]["AC"]
                    counters[signature] = max(counters.get(signature, 0), count)
                signatures = set(counters) | parents
                candidates[index]["AS"] = min(signatures, key=hashes.__getitem__)
                candidates[index]["AC"] = len(parents) + sum(six.itervalues(counters))
            for index in reversed(linearization):
                children = candidates[index].children
                if not children:
                    candidates[index]["DS"] = None
                    candidates[index]["DC"] = 0
                    continue
                counters = {}
                for child in children:
                    signature = candidates[child]["DS"]
                    if signature is None:
                        continue
                    count = candidates[child]["DC"]
                    counters[signature] = max(counters.get(signature, 0), count)
                signatures = set(counters) | children
                candidates[index]["DS"] = min(signatures, key=hashes.__getitem__)
                candidates[index]["DC"] = len(children) + sum(six.itervalues(counters))
            for index in candidates:
                ac, dc = candidates[index]["AC"], candidates[index]["DC"]
                candidates[index]["V"] = ac * dc + max(ac, dc)
            victims = sorted(candidates, key=(lambda i: -candidates[i]["V"]))
            black, white = set(), set()
            for victim in victims:
                volume = candidates[victim]["V"]
                if volume < 3:
                    break
                target = tasks[victim].target
                dead = (
                    target is None
                    or victim in black or victim in white
                    or candidates[victim]["AS"] in black or candidates[victim]["DS"] in white
                )
                if dead:
                    continue
                logging.getLogger(__name__).debug("Cutting at %r of volume %d", target, volume)
                try:
                    completed = yield deferrable(target.check).defer()
                except Exception as error:
                    logging.getLogger(__name__).warning("Failed to check %r: %s", target, error)
                else:
                    if completed:
                        logging.getLogger(__name__).debug("Blacklisting ancestors")
                        black.add(victim)
                        black |= candidates.trace(victim, "A")
                    else:
                        logging.getLogger(__name__).debug("Whitelisting descendants")
                        white.add(victim)
                        white |= candidates.trace(victim, "D")
            if not black and not white:
                break
            candidates.remove(*(black | white))
            linearization = [index for index in linearization if index in candidates]
            workflow.remove(*(tasks[index] for index in black))
            logging.getLogger(__name__).debug("Tasks left: %d", len(workflow))
        logging.getLogger(__name__).debug("Tasks after trimming: %d", len(workflow))
