import collections
import datetime
import functools
import hashlib
import re
import time
import weakref

import iso8601
import six

from edera.routine import routine


def memoized(function):
    """
    Enable memoization for the given function.

    Memoization allows you to cache return values of a function.

    This implementation assumes that all arguments of the function are hashable.
    The function must also be free of any major side-effects.

    You can apply this decorator to both functions and methods.

    Args:
        function (Callable) - a function that accepts no keyword arguments

    Returns:
        Callable - a memoized version of the function
    """

    class Memoizer(object):

        __instance_memos = weakref.WeakKeyDictionary()

        def __call__(self, *args):
            try:
                return self.__memo[args]
            except KeyError:
                self.__memo[args] = result = self.__function(*args)
                return result

        def __get__(self, owner, owner_type=None):
            if owner is None:
                return self
            instance_memo = self.__get_instance_memo(owner)
            instance_method = functools.partial(self.__function, owner)
            return Memoizer(instance_method, instance_memo)

        def __init__(self, function, memo):
            self.__function = function
            self.__memo = memo

        def __get_instance_memo(self, owner):
            try:
                return self.__instance_memos[owner]
            except KeyError:
                self.__instance_memos[owner] = result = {}
                return result

    return six.wraps(function)(Memoizer(function, {}))


def now():
    """
    Get current time in the UTC time zone.

    Returns:
        DateTime
    """
    return datetime.datetime.now(iso8601.iso8601.UTC)


def render(value):
    """
    Render the given value to a human-readable (multi-line) string.

    Suits well for writing stuff to a log.

    Args:
        value (Any) - a value to render
            Currently supported:
              - Mapping
              - Iterable

    Returns:
        String

    Raises:
        NotImplementedError if the given value type is not supported
    """
    if isinstance(value, collections.Mapping):
        return "".join("\n * %r => %r" % (key, value) for key, value in six.iteritems(value))
    if isinstance(value, collections.Iterable):
        return "".join("\n * %r" % element for element in value)
    raise NotImplementedError


def sha1(string):
    """
    Compute the SHA-1 hash of the string.

    Args:
        string (String) - a string to hash

    Returns:
        String - the hexadecimal representation of the SHA-1 hash of the string
    """
    return hashlib.sha1(string.encode("ASCII")).hexdigest()


@routine
def sleep(duration, measure=datetime.timedelta(seconds=1)):
    """
    Sleep for the given period of time, interrupting from time to time.

    Allows to create interruptible sleeps.

    Args:
        duration (TimeDelta) - a period of time to sleep for
        measure (TimeDelta) - a maximum delay between interruptions
            Default is 1 second.
    """
    start_time = datetime.datetime.utcnow()
    sleep_time = datetime.timedelta(milliseconds=10)
    while True:
        elapsed_time = datetime.datetime.utcnow() - start_time
        if elapsed_time >= duration:
            return
        yield
        time.sleep(sleep_time.total_seconds())
        sleep_time = min(2 * sleep_time, measure, duration - elapsed_time)


def squash_strings(strings):
    """
    Shorten strings in the list without losing too much meaning.

    Operates by tokenizing strings (splitting into alphanumeric parts) and pruning common prefixes.
    Assumes that the first word is the most important.
    Resulting strings may contain line separators.

    Args:
        strings (List[String]) - a list of distinct non-empty strings

    Returns:
        Iterable[String] - a set of shortened non-empty strings

    Raises:
        AssertionError if strings are not distinct or some them are empty
    """

    def get_common_prefix_length(tokenized_strings):
        zipped_tokenized_strings = list(zip(*tokenized_strings))
        result = 0
        while result < len(zipped_tokenized_strings):
            tokens = zipped_tokenized_strings[result]
            if tokens.count(tokens[0]) != len(tokens):
                break
            result += 1
        return result

    def squash_tokenized_strings(tokenized_strings, full=True):
        if not tokenized_strings:
            return []
        common_prefix_length = get_common_prefix_length(tokenized_strings)
        global_prefix = () if full or common_prefix_length == 0 else tokenized_strings[0][:1]
        tokenized_strings = [
            tokenized_string[common_prefix_length:]
            for tokenized_string in tokenized_strings
        ]
        groups = collections.defaultdict(list)
        indices = {}
        for tokenized_string in tokenized_strings:
            prefix = tokenized_string[:1]
            indices[tokenized_string] = len(groups[prefix])
            groups[prefix].append(tokenized_string[1:])
        for prefix in groups:
            if not prefix:
                continue
            groups[prefix] = squash_tokenized_strings(groups[prefix])
        return [
            (
                global_prefix
                + tokenized_string[:1]
                + groups[tokenized_string[:1]][indices[tokenized_string]]
            )
            for tokenized_string in tokenized_strings
        ]

    def tokenize_string(string):
        return tuple(filter(None, re.split("[^A-Za-z0-9_-]+", string)))

    assert len(set(strings)) == len(strings)
    assert all(strings)
    tokenized_input_strings = [tokenize_string(string) for string in strings]
    counter = collections.Counter(tokenized_input_strings)
    for index, tokenized_input_string in enumerate(tokenized_input_strings):
        if not tokenized_input_string or counter[tokenized_input_string] > 1:
            tokenized_input_strings[index] = (strings[index],)
    squashed_tokenized_input_strings = squash_tokenized_strings(tokenized_input_strings, full=False)
    for squashed_tokenized_input_string in squashed_tokenized_input_strings:
        yield "\n".join(squashed_tokenized_input_string)
