"""
This module implements various built-in qualifiers.
"""

import collections
import datetime
import re

import iso8601
import six

from edera.exceptions import ValueQualificationError
from edera.helpers import Factory
from edera.qualifier import Qualifier


class Any(Qualifier):
    """
    A qualifier that accepts any values.

    It provides the value as-is and uses $repr to obtain its representation.
    """

    @staticmethod
    def qualify(value):
        return (value, repr(value))


class Boolean(Qualifier):
    """
    A qualifier that accepts only boolean values.

    In other aspects, works as $Any.
    """

    @staticmethod
    def qualify(value):
        if not isinstance(value, bool):
            raise ValueQualificationError(value, "not a boolean")
        return (value, repr(value))


class Date(Qualifier):
    """
    A qualifier that accepts
      - $datetime.date objects as-is
      - strings in ISO 8601 format, "yyyy-mm-dd"
    and then represents them in ISO 8601 format.

    Does not accept $datetime.datetime objects!
    Convert them to $datetime.date by calling their $date method first.

    Constants:
        PATTERN (RegularExpression) - the pattern for ISO 8601 date format
    """

    PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    @staticmethod
    def qualify(value):
        if isinstance(value, six.string_types):
            if Date.PATTERN.match(value) is None:
                raise ValueQualificationError(value, "not in ISO 8601 format")
            value = iso8601.parse_date(value).date()
        if not isinstance(value, datetime.date) or isinstance(value, datetime.datetime):
            raise ValueQualificationError(value, "not a date")
        return (value, value.isoformat())


class DateTime(Qualifier):
    """
    A qualifier that accepts
      - "aware" (not "naive") $datetime.datetime objects
      - strings in ISO 8601 format, "yyyy-mm-ddThh:mm:ss[.ffffff]z"
    and then represents them in ISO 8601 format.

    Preserves the time zone.
    You can use $iso8601.iso8601.UTC or $iso8601.iso8601.FixedOffset to set up the time zone.

    Does not accept $datetime.date objects!

    Constants:
        PATTERN (RegularExpression) - the pattern for ISO 8601 date/time format
    """

    PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{6})?(Z|[+-]\d{2}:\d{2})$")

    @staticmethod
    def qualify(value):
        if isinstance(value, six.string_types):
            if DateTime.PATTERN.match(value) is None:
                raise ValueQualificationError(value, "not in ISO 8601 format")
            try:
                value = iso8601.parse_date(value, default_timezone=None)
            except ValueError as error:
                raise ValueQualificationError(value, str(error))
        if not isinstance(value, datetime.datetime):
            raise ValueQualificationError(value, "not a date/time")
        try:
            offset = value.utcoffset()
        except ValueError:
            raise ValueQualificationError(value, "invalid UTC offset")
        if offset is None:
            raise ValueQualificationError(value, "unknown time zone")
        utc = value.astimezone(iso8601.iso8601.UTC)
        representation = utc.replace(tzinfo=None).isoformat() + "Z"
        return (value, representation)


class DiscreteDateTime(Qualifier):
    """
    A date-time qualifier that quantizes input values.

    Rounds values down to the beginning of the containing interval.
    Intervals start from 1970-01-09T00:00:00 in the value's time zone.
    Intervals are also shifted by the given offset.

    Acts exactly like $DateTime in other aspects.

    Attributes:
        interval (TimeDelta)
        offset (TimeDelta)

    Constants:
        EPOCH (DateTime) - a "naive" Unix epoch
    """

    EPOCH = datetime.datetime.utcfromtimestamp(0)

    def __init__(self, interval, offset="P4D"):
        """
        Args:
            interal (TimeDelta)
            offset (TimeDelta)
                Default is 4 days, which skips to the first Monday since the Unix epoch.
        """
        self.interval = TimeDelta.qualify(interval)[0]
        self.offset = TimeDelta.qualify(offset)[0]

    def qualify(self, value):
        value = DateTime.qualify(value)[0]
        start = self.EPOCH + self.offset
        span = value.replace(tzinfo=None) - start
        count = int(span.total_seconds() / self.interval.total_seconds())
        return DateTime.qualify((start + count * self.interval).replace(tzinfo=value.tzinfo))


class Instance(Factory[Qualifier]):
    """
    A factory of qualifiers that check whether the value is an instance of a certain class.

    In other aspects, works as $Any.
    """

    @classmethod
    def qualify(cls, value):
        value_class = cls.cargo
        if not isinstance(value, value_class):
            raise ValueQualificationError(value, "not an instance of %r" % value_class)
        return (value, repr(value))


class Integer(Qualifier):
    """
    A qualifier that accepts only integer values.

    It provides the value as-is and represents it in the standard decimal format.
    """

    @staticmethod
    def qualify(value):
        if not isinstance(value, six.integer_types):
            raise ValueQualificationError(value, "not an integer")
        return (value, "%d" % value)


class List(Factory[Qualifier]):
    """
    A factory of qualifiers that check whether the value is iterable and contains
    suitable elements.

    It provides the value as a Python list and represents it as a comma-separated list
    in square brackets.
    """

    @classmethod
    def qualify(cls, value):
        element_qualifier = cls.cargo
        if not isinstance(value, collections.Iterable):
            raise ValueQualificationError(value, "not iterable")
        element_qualifications = list(map(element_qualifier.qualify, value))
        value = [element for element, _ in element_qualifications]
        representations = [element for _, element in element_qualifications]
        return (value, "[%s]" % ", ".join(representations))


class Mapping(Factory[Qualifier]):
    """
    A factory of qualifiers that check whether the value is a mapping and contains
    suitable key-element pairs.

    It provides the value as a Python dictionary and represents it as a comma-separated list
    of colon-separated key-element pairs in curly brackets.
    """

    @classmethod
    def qualify(cls, value):
        key_qualifier, element_qualifier = cls.cargo
        if not isinstance(value, collections.Mapping):
            raise ValueQualificationError(value, "not a mapping")
        key_element_pair_qualifications = [
            (key_qualifier.qualify(key), element_qualifier.qualify(element))
            for key, element in six.iteritems(value)
        ]
        value = {
            key: element
            for (key, _), (element, _) in key_element_pair_qualifications
        }
        representations = [
            "%s: %s" % (key, element)
            for (_, key), (_, element) in key_element_pair_qualifications
        ]
        representation = "{%s}" % ", ".join(sorted(representations))
        return (value, representation)


class Optional(Factory[Qualifier]):
    """
    A factory of qualifiers that allow $None values.

    Such a qualifier uses an underlying qualifier to qualify non-$None values.
    """

    @classmethod
    def qualify(cls, value):
        qualifier = cls.cargo
        if value is None:
            return Any.qualify(value)
        return qualifier.qualify(value)


class Set(Factory[Qualifier]):
    """
    A factory of qualifiers that check whether the value is iterable and contains
    suitable elements.

    Makes sure that all elements are hashable and comparable.

    It provides the value as a Python frozenset and represents it as a comma-separated list
    in curly brackets.
    """

    @classmethod
    def qualify(cls, value):
        element_qualifier = cls.cargo
        if not isinstance(value, collections.Iterable):
            raise ValueQualificationError(value, "not iterable")
        element_qualifications = list(map(element_qualifier.qualify, value))
        try:
            value = frozenset(element for element, _ in element_qualifications)
        except TypeError:
            raise ValueQualificationError(value, "elements are unhashable/incomparable")
        representations = [element for _, element in element_qualifications]
        return (value, "{%s}" % ", ".join(sorted(representations)))


class String(Qualifier):
    """
    A qualifier that accepts only ASCII strings.

    Also tries to convert the value from binary and Unicode forms.
    Uses $repr to obtain resulting string representation.
    """

    @staticmethod
    def qualify(value):
        try:
            if isinstance(value, six.text_type):
                value = value.encode("ASCII")
            if isinstance(value, six.binary_type):
                value = value.decode("ASCII")
        except (UnicodeDecodeError, UnicodeEncodeError):
            raise ValueQualificationError(value, "not an ASCII string")
        # now $value should be in ASCII-compatible Unicode
        if not isinstance(value, six.text_type):
            raise ValueQualificationError(value, "not a string")
        if not isinstance(value, str):  # specially for Python 2
            value = value.encode("ASCII")
        return (value, repr(value))


class Text(Qualifier):
    """
    A qualifier that accepts only Unicode strings.

    Also tries to convert the value from binary and encoded forms (ASCII only).
    Resulting string representation is a bit tricky (see the code).
    """

    @staticmethod
    def qualify(value):
        try:
            if isinstance(value, six.binary_type):
                value = value.decode("ASCII")
        except UnicodeDecodeError:
            raise ValueQualificationError(value, "should be Unicode or ASCII")
        if not isinstance(value, six.text_type):
            raise ValueQualificationError(value, "not a string")
        escaped_value = value.encode("UNICODE-ESCAPE")
        if not isinstance(escaped_value, str):  # specially for Python 3
            escaped_value = escaped_value.decode("ASCII")
        return (value, repr(escaped_value))


class TimeDelta(Qualifier):
    """
    A qualifier that accepts
      - $datetime.timedelta objects as-is
      - strings in restricted ISO 8601 format, "P[wW][dD][T[hH][mM][sS]]"
    and then represents them in ISO 8601 format.

    Does not accept $datetime.datetime objects!

    Constants:
        PATTERN (RegularExpression) - the pattern for ISO 8601 duration format
    """

    PATTERN = re.compile(
        (
            "^P"
            "((?P<weeks>{0})W)?"
            "((?P<days>{0})D)?"
            "(T"
            "((?P<hours>{0})H)?"
            "((?P<minutes>{0})M)?"
            "((?P<seconds>{0})S)?"
            ")?$"
        ).format(r"\d+(\.\d+)?"))

    @staticmethod
    def qualify(value):
        if isinstance(value, six.string_types):
            match = TimeDelta.PATTERN.match(value)
            if match is None:
                raise ValueQualificationError(value, "not in ISO 8601 format")
            measures = {
                name: float(measure)
                for name, measure in six.iteritems(match.groupdict(default="0"))
            }
            value = datetime.timedelta(**measures)
        if not isinstance(value, datetime.timedelta):
            raise ValueQualificationError(value, "not a duration")
        if value.total_seconds() < 0:
            raise ValueQualificationError(value, "duration is negative")
        return (value, ("PT%1.6fS" if value.microseconds else "PT%dS") % value.total_seconds())
