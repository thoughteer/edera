import abc
import re

import six


@six.add_metaclass(abc.ABCMeta)
class TestSelector(object):
    """
    An interface for test selectors.

    Test selectors are used to select testing scenarios associated with a particular task
    in a workflow.
    """

    @abc.abstractmethod
    def select(self, workflow, subject):
        """
        Select testing scenarios associated with the subject in the workflow.

        Args:
            workflow (Graph) - a graph of tasks
            subject (Task) - a subject task to select tests for (part of the workflow)

        Returns:
            Iterable[Scenario]
        """


class AllTestSelector(TestSelector):
    """
    A test selector that selects all testing scenarios from the "tests" annotation of the node.

    See also:
        $TestableTask
    """

    def select(self, workflow, subject):
        return workflow[subject].annotation.get("tests", [])


class RegexTestSelector(TestSelector):
    """
    A test selector that selects testing scenarios from the "tests" annotation of the node which
    match one of applicable regular expressions.

    See also:
        $TestableTask
    """

    def __init__(self, regexes):
        """
        Args:
            regexes (List[Tuple[String, String]]) - pairs of regular expressions
                The first regex is used to match the name of the subject,
                the second one - to match the name of the scenario.
        """
        self.__regexes = regexes

    def select(self, workflow, subject):
        for scenario in AllTestSelector().select(workflow, subject):
            if self.__match(subject, scenario):
                yield scenario

    def __match(self, subject, scenario):
        return any(self.__match_regex(regex, subject, scenario) for regex in self.__regexes)

    def __match_regex(self, regex, subject, scenario):
        return re.match(regex[0], subject.name) and re.match(regex[1], scenario.name)
