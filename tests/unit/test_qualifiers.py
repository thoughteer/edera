import datetime

import iso8601
import pytest
import six

from edera.exceptions import ValueQualificationError
from edera.qualifiers import Any
from edera.qualifiers import Boolean
from edera.qualifiers import Date
from edera.qualifiers import DateTime
from edera.qualifiers import DiscreteDateTime
from edera.qualifiers import Instance
from edera.qualifiers import Integer
from edera.qualifiers import List
from edera.qualifiers import Mapping
from edera.qualifiers import Optional
from edera.qualifiers import Set
from edera.qualifiers import String
from edera.qualifiers import Text
from edera.qualifiers import TimeDelta


def test_any_qualifier_works_correctly():
    assert Any.qualify("123") == ("123", repr("123"))
    assert Any.qualify([1, 2, 3]) == ([1, 2, 3], repr([1, 2, 3]))


def test_instance_qualifier_works_correctly():
    assert Instance[int].qualify(123) == (123, repr(123))
    assert Instance[list].qualify([1, 2, 3]) == ([1, 2, 3], repr([1, 2, 3]))
    with pytest.raises(ValueQualificationError):
        Instance[list].qualify(123)
    with pytest.raises(ValueQualificationError):
        Instance[str].qualify([1, 2, 3])
    with pytest.raises(ValueQualificationError):
        Instance[int].qualify("123")


def test_integer_qualifier_works_correctly():
    assert Integer.qualify(123) == (123, "123")
    assert Integer.qualify(-123) == (-123, "-123")
    with pytest.raises(ValueQualificationError):
        Integer.qualify(+123.4)
    with pytest.raises(ValueQualificationError):
        Integer.qualify("123")
    with pytest.raises(ValueQualificationError):
        Integer.qualify(None)


def test_integer_qualifier_handles_longs_correctly():
    if not six.PY2:
        return
    assert Integer.qualify(long(123)) == (long(123), "123")  # not "123L"


def test_list_qualifier_works_correctly():
    assert List[Integer].qualify([]) == ([], "[]")
    assert List[Integer].qualify([1, 2, 3]) == ([1, 2, 3], "[1, 2, 3]")
    assert List[List[Integer]].qualify([[1, 2], [3], []]) == (
        [[1, 2], [3], []],
        "[[1, 2], [3], []]",
    )
    with pytest.raises(ValueQualificationError):
        List[Integer].qualify([1, 2, "3"])
    with pytest.raises(ValueQualificationError):
        List[Integer].qualify(123)


def test_list_qualifier_accepts_arbitrary_iterables():
    assert List[Integer].qualify((1, 2)) == ([1, 2], "[1, 2]")
    assert List[Integer].qualify((x for x in range(3))) == ([0, 1, 2], "[0, 1, 2]")


def test_mapping_qualifier_works_correctly():
    assert Mapping[Integer, List[Integer]].qualify({}) == ({}, "{}")
    assert Mapping[Integer, List[Integer]].qualify({2: [2], 1: [1]}) == (
        {2: [2], 1: [1]},
        "{1: [1], 2: [2]}",
    )
    with pytest.raises(ValueQualificationError):
        Mapping[Integer, List[Integer]].qualify({1: [1], 2: [None]})
    with pytest.raises(ValueQualificationError):
        Mapping[Integer, List[Integer]].qualify({1: [1], 2: None})
    with pytest.raises(ValueQualificationError):
        Mapping[Integer, List[Integer]].qualify({"1": [2, 3]})
    with pytest.raises(ValueQualificationError):
        Mapping[Integer, List[Integer]].qualify([1, 2, 3])
    with pytest.raises(ValueQualificationError):
        Mapping[Integer, List[Integer]].qualify(123)


def test_set_qualifier_works_correctly():
    assert Set[Integer].qualify([]) == (set(), "{}")
    assert Set[Integer].qualify([3, 2, 1]) == ({1, 2, 3}, "{1, 2, 3}")
    with pytest.raises(ValueQualificationError):
        Set[Integer].qualify([1, 2, "3"])
    with pytest.raises(ValueQualificationError):
        Set[Integer].qualify(123)


def test_set_qualifier_produces_frozen_set():
    assert Set[Set[Integer]].qualify([[3, 2], [1], []]) == (
        set(map(frozenset, [{3, 2}, {1}, ()])),
        "{{1}, {2, 3}, {}}",
    )


def test_set_qualifier_fails_on_unhashable_elements():
    with pytest.raises(ValueQualificationError):
        Set[List[Integer]].qualify([[1], []])


def test_string_qualifier_works_correctly():
    assert String.qualify("hello") == ("hello", "'hello'")
    assert String.qualify(six.b("hello")) == ("hello", "'hello'")  # not "u'hello'"
    assert String.qualify(six.u("hello")) == ("hello", "'hello'")  # not "b'hello'"
    with pytest.raises(ValueQualificationError):
        String.qualify(six.b("\xd0\xbf\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82").decode("UTF-8"))
    with pytest.raises(ValueQualificationError):
        String.qualify(six.b("\xd0\xbf\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82"))
    with pytest.raises(ValueQualificationError):
        String.qualify([1, 2, 3])
    with pytest.raises(ValueQualificationError):
        String.qualify(123)


def test_string_qualifier_escapes_quotes_consistently():
    assert String.qualify("'hello'") == ("'hello'", "\"'hello'\"")
    assert String.qualify("'hello\"") == ("'hello\"", "'\\'hello\"'")


def test_text_qualifier_works_correctly():
    assert Text.qualify(six.u("hello")) == (six.u("hello"), "'hello'")
    assert Text.qualify(six.b("hello")) == (six.u("hello"), "'hello'")
    assert Text.qualify("hello") == (six.u("hello"), "'hello'")
    hello = six.b("\xd0\xbf\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82")
    assert Text.qualify(hello.decode("UTF-8"))[0].encode("UTF-8") == hello
    assert Text.qualify(hello.decode("UTF-8"))[1] == r"'\\u043f\\u0440\\u0438\\u0432\\u0435\\u0442'"
    with pytest.raises(ValueQualificationError):
        Text.qualify(hello)
    with pytest.raises(ValueQualificationError):
        Text.qualify([1, 2, 3])
    with pytest.raises(ValueQualificationError):
        Text.qualify(123)


def test_optional_qualifier_accepts_none_values():
    assert Optional[String].qualify(None) == (None, "None")


def test_optional_qualifier_uses_underlying_qualifier():
    assert Optional[String].qualify("hello") == ("hello", "'hello'")
    with pytest.raises(ValueQualificationError):
        Optional[String].qualify(123)


def test_boolean_qualifier_works_correctly():
    assert Boolean.qualify(True) == (True, "True")
    assert Boolean.qualify(False) == (False, "False")
    with pytest.raises(ValueQualificationError):
        Boolean.qualify("")


def test_date_qualifier_accepts_date_objects_from_standard_library():
    assert Date.qualify(datetime.date(2017, 3, 15)) == (datetime.date(2017, 3, 15), "2017-03-15")


def test_date_qualifier_does_not_accept_datetime_objects():
    with pytest.raises(ValueQualificationError):
        Date.qualify(datetime.datetime(2017, 3, 15))


def test_date_qualifier_accepts_strings_in_strict_iso8601_format():
    assert Date.qualify("2017-03-15") == (datetime.date(2017, 3, 15), "2017-03-15")
    with pytest.raises(ValueQualificationError):
        Date.qualify("2017-3-15")
    with pytest.raises(ValueQualificationError):
        Date.qualify("20170315")
    with pytest.raises(ValueQualificationError):
        Date.qualify("03-15-2017")
    with pytest.raises(ValueQualificationError):
        Date.qualify("2017-03-15T00:00:00Z")
    with pytest.raises(ValueQualificationError):
        Date.qualify("0000-00-00")


def test_datetime_qualifier_accepts_datetime_objects_from_standard_library():
    assert DateTime.qualify(
            datetime.datetime(2017, 3, 15, 10, 6, 2, 789, tzinfo=iso8601.iso8601.UTC)) == (
        datetime.datetime(2017, 3, 15, 10, 6, 2, 789, tzinfo=iso8601.iso8601.UTC),
        "2017-03-15T10:06:02.000789Z",
    )


def test_datetime_qualifier_does_not_accept_date_objects():
    with pytest.raises(ValueQualificationError):
        DateTime.qualify(datetime.date(2017, 3, 15))


def test_datetime_qualifier_does_not_accept_naive_datetime_objects():
    with pytest.raises(ValueQualificationError):
        DateTime.qualify(datetime.datetime(2017, 3, 15))


def test_datetime_qualifier_accepts_strings_in_strict_iso8601_format():
    assert DateTime.qualify("2017-03-15T10:06:02Z") == (
        datetime.datetime(2017, 3, 15, 10, 6, 2, 0, tzinfo=iso8601.iso8601.UTC),
        "2017-03-15T10:06:02Z",
    )
    assert DateTime.qualify("2017-03-15T10:06:02.000789Z") == (
        datetime.datetime(2017, 3, 15, 10, 6, 2, 789, tzinfo=iso8601.iso8601.UTC),
        "2017-03-15T10:06:02.000789Z",
    )
    assert DateTime.qualify("2017-03-15T10:06:02.000789+03:00") == (
        datetime.datetime(
            2017, 3, 15, 10, 6, 2, 789, tzinfo=iso8601.iso8601.FixedOffset(3, 0, "+03:00")),
        "2017-03-15T07:06:02.000789Z",
    )
    assert DateTime.qualify("2017-03-15T10:06:02.000789-11:30") == (
        datetime.datetime(
            2017, 3, 15, 10, 6, 2, 789, tzinfo=iso8601.iso8601.FixedOffset(-11, -30, "-11:30")),
        "2017-03-15T21:36:02.000789Z",
    )
    with pytest.raises(ValueQualificationError):
        DateTime.qualify("2017-03-15")
    with pytest.raises(ValueQualificationError):
        DateTime.qualify("2017-03-15T10:06:02")
    with pytest.raises(ValueQualificationError):
        DateTime.qualify("2017-03-15 10:06:02Z")
    with pytest.raises(ValueQualificationError):
        DateTime.qualify("2017-03-15T10:06:02-25:00")
    with pytest.raises(ValueQualificationError):
        DateTime.qualify("0000-00-00T00:00:00Z")


def test_timedelta_qualifier_accepts_timedelta_objects_from_standard_library():
    assert TimeDelta.qualify(datetime.timedelta(seconds=0.123456)) == (
        datetime.timedelta(seconds=0.123456),
        "PT0.123456S",
    )
    assert TimeDelta.qualify(datetime.timedelta(days=1)) == (datetime.timedelta(days=1), "PT86400S")
    assert TimeDelta.qualify(datetime.timedelta(days=1, seconds=0.123456)) == (
        datetime.timedelta(days=1, seconds=0.123456),
        "PT86400.123456S",
    )
    with pytest.raises(ValueQualificationError):
        TimeDelta.qualify(datetime.timedelta(days=-1, hours=23))


def test_timedelta_qualifier_does_not_accept_datetime_objects():
    with pytest.raises(ValueQualificationError):
        TimeDelta.qualify(datetime.datetime(2017, 3, 15, 10, 6, 2))


def test_timedelta_qualifier_accepts_strings_in_strict_iso8601_format():
    assert TimeDelta.qualify("P1.1W2.2DT3.3H4.4M5.5S") == (
        datetime.timedelta(weeks=1.1, days=2.2, hours=3.3, minutes=4.4, seconds=5.5),
        "PT867509.500000S",
    )
    assert TimeDelta.qualify("P1WT12H") == (datetime.timedelta(weeks=1, hours=12),  "PT648000S")
    assert TimeDelta.qualify("P6D") == (datetime.timedelta(days=6), "PT518400S")
    assert TimeDelta.qualify("P") == (datetime.timedelta(), "PT0S")
    with pytest.raises(ValueQualificationError):
        TimeDelta.qualify("P1Y")
    with pytest.raises(ValueQualificationError):
        TimeDelta.qualify("P1M")
    with pytest.raises(ValueQualificationError):
        TimeDelta.qualify("0")


def test_discretedatetime_qualifier_works_with_week_intervals():
    tz = iso8601.iso8601.FixedOffset(3, 0, "MSK")
    assert DiscreteDateTime("P7D").qualify(
            datetime.datetime(2017, 3, 15, 2, 6, 2, 789, tzinfo=tz)) == (
        datetime.datetime(2017, 3, 13, tzinfo=tz),
        "2017-03-12T21:00:00Z",
    )


def test_discretedatetime_qualifier_works_with_day_intervals():
    tz = iso8601.iso8601.FixedOffset(3, 0, "MSK")
    assert DiscreteDateTime("P1D").qualify(
            datetime.datetime(2017, 3, 15, 2, 6, 2, 789, tzinfo=tz)) == (
        datetime.datetime(2017, 3, 15, tzinfo=tz),
        "2017-03-14T21:00:00Z",
    )


def test_discretedatetime_qualifier_works_with_hour_intervals():
    tz = iso8601.iso8601.FixedOffset(3, 0, "MSK")
    assert DiscreteDateTime("PT1H", offset="PT30M").qualify(
            datetime.datetime(2017, 3, 15, 2, 6, 2, 789, tzinfo=tz)) == (
        datetime.datetime(2017, 3, 15, 1, 30, tzinfo=tz),
        "2017-03-14T22:30:00Z",
    )


def test_discretedatetime_qualifier_works_with_minute_intervals():
    tz = iso8601.iso8601.FixedOffset(3, 0, "MSK")
    assert DiscreteDateTime("PT5M").qualify(
            datetime.datetime(2017, 3, 15, 2, 6, 2, 789, tzinfo=tz)) == (
        datetime.datetime(2017, 3, 15, 2, 5, tzinfo=tz),
        "2017-03-14T23:05:00Z",
    )
