from datetime import datetime, timedelta, timezone

import pytest

from datetime_normalizer import (
    AmbiguousDatetimeError,
    DateOrder,
    DatetimeNormalizer,
    DatetimePrecision,
    InvalidDatetimeError,
    NormalizedDatetime,
    UnrecognizedDatetimeError,
)


@pytest.fixture
def normalizer() -> DatetimeNormalizer:
    return DatetimeNormalizer()


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # Numeric dates
        ("2024-01-05", "2024-01-05"),
        ("2024/1/5", "2024-01-05"),
        ("2024.1.5", "2024-01-05"),
        ("2024:01:05", "2024-01-05"),
        ("20240105", "2024-01-05"),
        ("２０２４／０１／０５", "2024-01-05"),
        ("2024ー01ー05", "2024-01-05"),
        # Partial dates
        ("2024", "2024"),
        ("2024-01", "2024-01"),
        ("2024年", "2024"),
        ("2024年1月", "2024-01"),
        # Japanese dates
        ("2024年1月5日", "2024-01-05"),
        ("2024 年 1 月 5 日", "2024-01-05"),
        ("２０２４年１月５日", "2024-01-05"),
        ("二〇二四年一月五日", "2024-01-05"),
        ("二千二十四年十二月三十一日", "2024-12-31"),
        # Eras
        ("令和6年1月5日", "2024-01-05"),
        ("令和六年一月五日", "2024-01-05"),
        ("令和元年5月1日", "2019-05-01"),
        ("平成31年4月30日", "2019-04-30"),
        ("昭和64年1月7日", "1989-01-07"),
        ("大正15年12月25日", "1926-12-25"),
        ("昭和元年12月25日", "1926-12-25"),
        ("明治45年7月30日", "1912-07-30"),
        ("大正元年7月30日", "1912-07-30"),
        ("明治6年1月1日", "1873-01-01"),
        ("平成31年4月", "2019-04"),
        ("令和元年", "2019"),
        ("㋿6年1月5日", "2024-01-05"),
        ("㍻31年4月30日", "2019-04-30"),
        ("R6.1.5", "2024-01-05"),
        ("r06/01/05", "2024-01-05"),
        ("H31-4-30", "2019-04-30"),
        ("H.31.4.30", "2019-04-30"),
        ("S64.1.7", "1989-01-07"),
        ("令6.1.5", "2024-01-05"),
        ("令和6.1", "2024-01"),
        ("R元.5.1", "2019-05-01"),
        ("R6年1月5日", "2024-01-05"),
        # English dates
        ("January 5, 2024", "2024-01-05"),
        ("Jan 5th 2024", "2024-01-05"),
        ("5 Jan 2024", "2024-01-05"),
        ("05-Sept-2024", "2024-09-05"),
        ("January 2024", "2024-01"),
        # Weekdays are verified and dropped
        ("2024年1月5日(金)", "2024-01-05"),
        ("2024年1月5日（金曜日）", "2024-01-05"),
        ("2024年1月5日 金曜", "2024-01-05"),
        ("2024年1月7日(日)", "2024-01-07"),
        ("Friday, January 5, 2024", "2024-01-05"),
        ("2024-01-05 (Fri)", "2024-01-05"),
        # Times
        ("2024-01-05T13", "2024-01-05T13"),
        ("2024-01-05 13:05", "2024-01-05T13:05"),
        ("2024-01-05T13:05:09", "2024-01-05T13:05:09"),
        ("2024-01-05 1:05", "2024-01-05T01:05"),
        ("2024-01-05T13:05:09.5", "2024-01-05T13:05:09.500000"),
        ("2024-01-05T13:05:09,123456789", "2024-01-05T13:05:09.123456"),
        ("20240105T130509", "2024-01-05T13:05:09"),
        ("20240105130509", "2024-01-05T13:05:09"),
        ("202401051305", "2024-01-05T13:05"),
        ("2024:01:05 13:05:09", "2024-01-05T13:05:09"),
        # Japanese times
        ("2024年1月5日13時", "2024-01-05T13"),
        ("2024年1月5日 13時5分", "2024-01-05T13:05"),
        ("2024年1月5日13時05分09秒", "2024-01-05T13:05:09"),
        ("2024年1月5日13時5分9.5秒", "2024-01-05T13:05:09.500000"),
        ("令和六年一月五日十三時五分", "2024-01-05T13:05"),
        ("2024年1月5日1時半", "2024-01-05T01:30"),
        ("2024年1月5日午後1時半", "2024-01-05T13:30"),
        ("2024年1月5日(金)午前9時", "2024-01-05T09"),
        ("2024年1月5日午後一時", "2024-01-05T13"),
        ("2024年1月5日午前0時", "2024-01-05T00"),
        ("2024年1月5日午後0時30分", "2024-01-05T12:30"),
        ("2024年1月5日午後1:30", "2024-01-05T13:30"),
        ("2024年1月5日正午", "2024-01-05T12:00"),
        # English 12-hour clock
        ("January 5, 2024 1:30 PM", "2024-01-05T13:30"),
        ("Jan 5, 2024, 1:30 p.m.", "2024-01-05T13:30"),
        ("2024-01-05 12:30 AM", "2024-01-05T00:30"),
        ("2024-01-05 12:30 PM", "2024-01-05T12:30"),
        ("2024-01-05 1pm", "2024-01-05T13"),
        # Hours past midnight move to the next day
        ("2024-01-05 24:00", "2024-01-06T00:00"),
        ("2024-12-31T24:00:00", "2025-01-01T00:00:00"),
        ("2024年2月28日25時", "2024-02-29T01"),
        ("2024年1月5日(金)25時30分", "2024-01-06T01:30"),
        # Time zones
        ("2024-01-05T13:05:09Z", "2024-01-05T13:05:09+00:00"),
        ("2024-01-05T13:05:09+09:00", "2024-01-05T13:05:09+09:00"),
        ("2024-01-05T13:05:09+0900", "2024-01-05T13:05:09+09:00"),
        ("2024-01-05T13:05:09+9", "2024-01-05T13:05:09+09:00"),
        ("2024-01-05T13:05-05:30", "2024-01-05T13:05-05:30"),
        ("2024-01-05 13:05 JST", "2024-01-05T13:05+09:00"),
        ("2024-01-05 13:05 UTC+9", "2024-01-05T13:05+09:00"),
        ("2024-01-05 13:05 GMT", "2024-01-05T13:05+00:00"),
        ("2024年1月5日13時5分 日本時間", "2024-01-05T13:05+09:00"),
        ("20240105T130509+0900", "2024-01-05T13:05:09+09:00"),
        ("2024-01-05 13:05+14:00", "2024-01-05T13:05+14:00"),
        ("2024-01-05T13:05-12:00", "2024-01-05T13:05-12:00"),
        # A range that fits the offsets in use cannot be told from a time zone.
        ("2024/1/5T09:00-12:00", "2024-01-05T09:00-12:00"),
        ("Fri, 05 Jan 2024 13:05:09 +0900", "2024-01-05T13:05:09+09:00"),
    ],
)
def test_normalize(normalizer: DatetimeNormalizer, text: str, expected: str) -> None:
    assert normalizer.normalize(text).isoformat() == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2024", DatetimePrecision.YEAR),
        ("2024年1月", DatetimePrecision.MONTH),
        ("2024/1/5", DatetimePrecision.DAY),
        ("2024/1/5 13時", DatetimePrecision.HOUR),
        ("2024/1/5 1時半", DatetimePrecision.MINUTE),
        ("2024/1/5 13:05:09", DatetimePrecision.SECOND),
        ("2024/1/5 13:05:09.1", DatetimePrecision.MICROSECOND),
    ],
)
def test_precision(normalizer: DatetimeNormalizer, text: str, expected: DatetimePrecision) -> None:
    assert normalizer.normalize(text).precision is expected


def test_value_fills_units_below_precision(normalizer: DatetimeNormalizer) -> None:
    assert normalizer.normalize("2024年3月").value == datetime(2024, 3, 1)


def test_time_zone_is_kept_only_when_stated(normalizer: DatetimeNormalizer) -> None:
    naive: NormalizedDatetime = normalizer.normalize("2024-01-05 13:05")
    aware: NormalizedDatetime = normalizer.normalize("2024-01-05 13:05 JST")

    assert not naive.is_timezone_aware
    assert aware.is_timezone_aware
    assert aware.value.tzinfo == timezone(timedelta(hours=9))


@pytest.mark.parametrize(
    "text",
    [
        "1/2/2024",
        "01-02-2024",
        "13/1/2024",
        "24/1/5",
        "24-01-05",
        "24年1月5日",
        "1月5日",
        "1月",
        "January 5",
        "2024年1月5日午後12時",
        "2024年1月5日午前12時30分",
    ],
)
def test_ambiguous_text_is_rejected(normalizer: DatetimeNormalizer, text: str) -> None:
    with pytest.raises(AmbiguousDatetimeError):
        _ = normalizer.normalize(text)


def test_date_order_decides_year_last_dates() -> None:
    month_first: DatetimeNormalizer = DatetimeNormalizer(date_order=DateOrder.MONTH_FIRST)
    day_first: DatetimeNormalizer = DatetimeNormalizer(date_order=DateOrder.DAY_FIRST)

    assert month_first.normalize("1/2/2024").isoformat() == "2024-01-02"
    assert day_first.normalize("1/2/2024").isoformat() == "2024-02-01"


def test_date_order_does_not_guess_when_it_does_not_fit() -> None:
    with pytest.raises(InvalidDatetimeError):
        _ = DatetimeNormalizer(date_order=DateOrder.MONTH_FIRST).normalize("13/1/2024")


@pytest.mark.parametrize(
    "text",
    [
        "2024-13-01",
        "2024-00-01",
        "2024-01-00",
        "2023-02-29",
        "2024年2月30日",
        "0000-01-01",
        # Outside the era
        "令和0年",
        "令和元年4月30日",
        "令和元年4月",
        "平成31年5月1日",
        "平成31年5月",
        "平成32年",
        "昭和64年1月8日",
        "平成元年1月7日",
        "大正16年",
        "明治5年12月31日",
        # Times that do not exist
        "2024-01-05 13:60",
        "2024-01-05 13:05:60",
        "2024-01-05 48:00",
        "2024年1月5日13時60分",
        "2024-01-05 13:05+24:00",
        "2024-01-05 13:05+09:60",
        "2024-01-05 13:05+14:01",
        "2024-01-05T13:05-12:01",
        "2024-01-05T13:00-15:00",
        "2024-01-05 13:00 PM",
        "2024-01-05 0:30 AM",
        "2024年1月5日午後13時",
        "9999-12-31 24:00",
        # Weekday contradicts the date
        "2024年1月5日(月)",
        "Monday, January 5, 2024",
    ],
)
def test_impossible_text_is_rejected(normalizer: DatetimeNormalizer, text: str) -> None:
    with pytest.raises(InvalidDatetimeError):
        _ = normalizer.normalize(text)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "hello",
        "13:05",
        "昨日",
        "202401",
        "2024010",
        "202401051",
        "20245年1月",
        "2024-01/05",
        "2024-1-5 extra",
        "2024-01-05 13:05 Mars/Olympus",
        "2024-01-05 13:05 火星時間",
        "2024-01-05 13:05 Factory",
        "2024 13:05",
        "2024年1月 13時",
        "2024年1月(月)",
        "2024-01-05 am 1:30 pm",
        "2024年1月5日午前1:30 PM",
        "2024年1月5日午後1時 am",
        "2024年1月十十日",
    ],
)
def test_unsupported_text_is_rejected(normalizer: DatetimeNormalizer, text: str) -> None:
    with pytest.raises(UnrecognizedDatetimeError):
        _ = normalizer.normalize(text)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1月5日", "2023-01-05"),
        ("１月５日", "2023-01-05"),
        ("一月五日", "2023-01-05"),
        ("1月", "2023-01"),
        ("January 5", "2023-01-05"),
        ("Jan. 5th", "2023-01-05"),
        ("5 Jan", "2023-01-05"),
        ("5-Sept", "2023-09-05"),
        ("1月5日13時5分", "2023-01-05T13:05"),
        ("1月5日(木)午後1時半", "2023-01-05T13:30"),
        ("Jan 5, 1:30 PM", "2023-01-05T13:30"),
        ("5 Jan 13:05 JST", "2023-01-05T13:05+09:00"),
        ("12月31日24時", "2024-01-01T00"),
        # A year in the text takes precedence.
        ("2024年1月5日", "2024-01-05"),
        ("令和6年1月5日", "2024-01-05"),
    ],
)
def test_default_year_fills_missing_year(
    normalizer: DatetimeNormalizer, text: str, expected: str
) -> None:
    assert normalizer.normalize(text, default_year=2023).isoformat() == expected


def test_date_order_decides_slash_dates_without_a_year() -> None:
    month_first: DatetimeNormalizer = DatetimeNormalizer(date_order=DateOrder.MONTH_FIRST)
    day_first: DatetimeNormalizer = DatetimeNormalizer(date_order=DateOrder.DAY_FIRST)

    assert month_first.normalize("1/2 13:05", default_year=2024).isoformat() == "2024-01-02T13:05"
    assert day_first.normalize("1/2", default_year=2024).isoformat() == "2024-02-01"


@pytest.mark.parametrize(
    "text",
    [
        "1/2",
        "5 Jan 24",
        "Jan 5, 24",
        "1月5日 24",
        "1月5日 1305",
        "5 Jan 24 JST",
        "5 Jan 24 +0900",
        "Jan 5, 24 +09:00",
        "1月5日 24 JST",
    ],
)
def test_unclear_text_without_a_year_is_rejected(normalizer: DatetimeNormalizer, text: str) -> None:
    with pytest.raises(AmbiguousDatetimeError):
        _ = normalizer.normalize(text, default_year=2024)


@pytest.mark.parametrize(
    ("text", "default_year"),
    [
        ("2月29日", 2023),
        ("13月1日", 2024),
        ("1月32日", 2024),
        ("1月5日(月)", 2024),
        ("1月5日", 0),
    ],
)
def test_impossible_date_with_default_year_is_rejected(
    normalizer: DatetimeNormalizer, text: str, default_year: int
) -> None:
    with pytest.raises(InvalidDatetimeError):
        _ = normalizer.normalize(text, default_year=default_year)


def test_leap_day_needs_a_leap_default_year(normalizer: DatetimeNormalizer) -> None:
    assert normalizer.normalize("2月29日", default_year=2024).isoformat() == "2024-02-29"


@pytest.mark.parametrize("text", ["1-5", "1.5", "5日", "1/5/", "January", "13:05", "Janus 5"])
def test_unsupported_text_without_a_year_is_rejected(
    normalizer: DatetimeNormalizer, text: str
) -> None:
    with pytest.raises(UnrecognizedDatetimeError):
        _ = normalizer.normalize(text, default_year=2024)
