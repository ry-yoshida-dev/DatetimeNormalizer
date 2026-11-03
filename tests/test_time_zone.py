from datetime import UTC, date, datetime, time, timedelta, timezone, tzinfo
from time import perf_counter
from typing import override
from zoneinfo import ZoneInfo

import pytest
from hypothesis import given
from hypothesis import strategies as st

from datetime_normalizer import (
    AmbiguousDatetimeError,
    DatetimeNormalizer,
    DatetimePrecision,
    InvalidConfigurationError,
    InvalidDatetimeError,
    NormalizedDatetime,
    UnrecognizedDatetimeError,
)

NORMALIZER: DatetimeNormalizer = DatetimeNormalizer()
ZONES: tuple[str, ...] = (
    "UTC",
    "Asia/Tokyo",
    "Asia/Kolkata",
    "Asia/Kathmandu",
    "America/New_York",
    "America/St_Johns",
    "Europe/London",
    "Australia/Lord_Howe",
    "Pacific/Kiritimati",
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # IANA names, in any case, follow daylight saving time
        ("2024-01-05 13:05 America/New_York", "2024-01-05T13:05-05:00"),
        ("2024-07-05 13:05 america/new_york", "2024-07-05T13:05-04:00"),
        ("2024-01-05 13:05 Asia/Kolkata", "2024-01-05T13:05+05:30"),
        ("2024-01-05 13:05 Etc/GMT+9", "2024-01-05T13:05-09:00"),
        ("2024-01-05 13:05 Japan", "2024-01-05T13:05+09:00"),
        # Abbreviations hold their fixed offset
        ("2024-01-05 13:05 EST", "2024-01-05T13:05-05:00"),
        ("2024-07-05 13:05 EST", "2024-07-05T13:05-05:00"),
        ("2024-07-05 13:05 EDT", "2024-07-05T13:05-04:00"),
        ("2024-07-05 1:05 PM CEST", "2024-07-05T13:05+02:00"),
        ("2024-01-05 13:05 NPT", "2024-01-05T13:05+05:45"),
        # Generic abbreviations follow daylight saving time
        ("2024-01-05 13:05 PT", "2024-01-05T13:05-08:00"),
        ("2024-07-05 13:05 PT", "2024-07-05T13:05-07:00"),
        # Japanese names, also before the time and in parentheses
        ("2024年1月5日13時 協定世界時", "2024-01-05T13+00:00"),
        ("2024年1月5日13時 グリニッジ標準時", "2024-01-05T13+00:00"),
        ("2024年7月5日13時 米国東部時間", "2024-07-05T13-04:00"),
        ("2024年1月5日13時 シンガポール時間", "2024-01-05T13+08:00"),
        ("2024年1月5日13時(日本時間)", "2024-01-05T13+09:00"),
        ("2024年1月5日 日本時間午後1時", "2024-01-05T13+09:00"),
        ("2024年1月5日(日本時間)13:05", "2024-01-05T13:05+09:00"),
        ("2024年1月5日(金) 日本時間13時半", "2024-01-05T13:30+09:00"),
        # A note on the offset, as RFC 9557 and JavaScript write them
        ("2024-01-05T13:05:00+09:00[Asia/Tokyo]", "2024-01-05T13:05:00+09:00"),
        ("2024-01-05T13:05:00+09:00[!Asia/Tokyo]", "2024-01-05T13:05:00+09:00"),
        ("Fri, 05 Jan 2024 13:05:09 +0900 (JST)", "2024-01-05T13:05:09+09:00"),
        ("Fri Jan 05 2024 13:05:09 GMT+0900 (日本標準時)", "2024-01-05T13:05:09+09:00"),
        # An offset settles a time that occurs twice
        ("2024-11-03 01:30-04:00[America/New_York]", "2024-11-03T01:30-04:00"),
        ("2024-11-03 01:30-05:00[America/New_York]", "2024-11-03T01:30-05:00"),
        # Seconds in an offset, from local mean time
        ("1800-01-01 09:18:59+09:18:59", "1800-01-01T09:18:59+09:18:59"),
    ],
)
def test_time_zone_notations(text: str, expected: str) -> None:
    assert NORMALIZER.normalize(text).isoformat() == expected


@pytest.mark.parametrize(
    "name",
    [
        "米国東部時間",
        "米国中部時間",
        "米国山岳部時間",
        "米国太平洋時間",
        "ニューヨーク時間",
        "シカゴ時間",
        "ロサンゼルス時間",
        "ハワイ時間",
        "ロンドン時間",
        "英国時間",
        "イギリス時間",
        "パリ時間",
        "フランス時間",
        "ベルリン時間",
        "ドイツ時間",
        "モスクワ時間",
        "インド時間",
        "インド標準時",
        "タイ時間",
        "ベトナム時間",
        "シンガポール時間",
        "香港時間",
        "台湾時間",
        "中国時間",
        "中国標準時",
        "北京時間",
        "韓国時間",
        "韓国標準時",
        "シドニー時間",
        "世界協定時",
        "世界標準時",
        "日本標準時",
        "東部標準時",
        "東部夏時間",
        "中部標準時",
        "中部夏時間",
        "山岳部標準時",
        "山岳部夏時間",
        "太平洋標準時",
        "太平洋夏時間",
    ],
)
def test_every_japanese_name_is_readable(name: str) -> None:
    assert NORMALIZER.normalize(f"2024年1月5日13時 {name}").is_time_zone_stated
    assert NORMALIZER.normalize(f"2024年1月5日 {name} 13時").is_time_zone_stated


@pytest.mark.parametrize(
    ("name", "offset"),
    [("ET", "-05:00"), ("CT", "-06:00"), ("MT", "-07:00"), ("PT", "-08:00")],
)
def test_generic_american_abbreviations(name: str, offset: str) -> None:
    assert NORMALIZER.normalize(f"2024-01-05 13:05 {name}").isoformat().endswith(offset)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2024-01-05 UTC 13:05", "2024-01-05T13:05+00:00"),
        ("2024-01-05 Asia/Tokyo 1:05 PM", "2024-01-05T13:05+09:00"),
        ("2024-01-05 (JST) 13時", "2024-01-05T13+09:00"),
    ],
)
def test_english_name_before_the_time(text: str, expected: str) -> None:
    assert NORMALIZER.normalize(text).isoformat() == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # A skipped time moves ahead by the skip.
        ("2024-03-10 02:30 America/New_York", "2024-03-10T03:30-04:00"),
        ("2024-03-31 01:30 Europe/London", "2024-03-31T02:30+01:00"),
        ("2024-03-09 26時 America/New_York", "2024-03-10T03-04:00"),
        # The hour grows to minutes when the skip is half an hour.
        ("2024-10-06 02時 Australia/Lord_Howe", "2024-10-06T02:30+11:00"),
        # A repeated time is the earlier one.
        ("2024-11-03 01:30 America/New_York", "2024-11-03T01:30-04:00"),
        ("2024-11-03 01:30 ET", "2024-11-03T01:30-04:00"),
        ("2024-10-27 01:30 Europe/London", "2024-10-27T01:30+01:00"),
        # Another zone tells which, whichever comes first.
        ("2024-11-03 01:30 ET (EST)", "2024-11-03T01:30-05:00"),
        # Time zones that disagree are a conversion from the first to the last.
        ("2024-01-05 13:05+08:00[Asia/Tokyo]", "2024-01-05T14:05+09:00"),
        ("2024-01-05T13:05Z[Asia/Tokyo]", "2024-01-05T22:05+09:00"),
        ("2024-01-05 13:05 UTC (日本時間)", "2024-01-05T22:05+09:00"),
        ("2024-01-05 13:05 JST (EST)", "2024-01-04T23:05-05:00"),
        ("2024年1月5日 日本時間13時 UTC", "2024-01-05T04+00:00"),
        ("2024-01-05 13時+09:00[Asia/Kolkata]", "2024-01-05T09:30+05:30"),
        ("2024-03-10 02:30-05:00[America/New_York]", "2024-03-10T03:30-04:00"),
        ("2024-11-03 01:30-03:00[America/New_York]", "2024-11-03T00:30-04:00"),
    ],
)
def test_times_moved_by_their_time_zone(text: str, expected: str) -> None:
    assert NORMALIZER.normalize(text).isoformat() == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("CST", "-06:00"),
        ("CDT", "-05:00"),
        ("MST", "-07:00"),
        ("PST", "-08:00"),
        ("AST", "-04:00"),
        ("ADT", "-03:00"),
        ("IST", "+05:30"),
        ("BST", "+01:00"),
        ("GST", "+04:00"),
        ("SST", "-11:00"),
        ("WST", "+13:00"),
        ("AMT", "-04:00"),
        ("BDT", "+06:00"),
        ("ECT", "-05:00"),
        ("世界時", "+00:00"),
        ("世界時間", "+00:00"),
    ],
)
def test_shared_names_mean_the_most_common_zone(name: str, expected: str) -> None:
    assert NORMALIZER.normalize(f"2024-01-05 13:05 {name}").isoformat().endswith(expected)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1704427200", "2024-01-05T04:00:00+00:00"),
        ("1704427200.5", "2024-01-05T04:00:00.500000+00:00"),
        ("1704427200000", "2024-01-05T04:00:00+00:00"),
        ("1704427200123", "2024-01-05T04:00:00.123000+00:00"),
        ("１７０４４２７２００", "2024-01-05T04:00:00+00:00"),
        # Compact dates and hours stay as they are.
        ("1999123113", "1999-12-31T13"),
        ("2024010513", "2024-01-05T13"),
        ("20240105", "2024-01-05"),
    ],
)
def test_unix_time(text: str, expected: str) -> None:
    assert NORMALIZER.normalize(text).isoformat() == expected


@pytest.mark.parametrize(
    "text",
    [
        "2024-01-05 13:05 +25:00",
        "2024-01-05 13:05 +09:60",
        "2024-01-05 13:05 +09:00:60",
        "0001-01-01 00:00+09:00[UTC]",
    ],
)
def test_impossible_time_zones_are_rejected(text: str) -> None:
    with pytest.raises(InvalidDatetimeError):
        _ = NORMALIZER.normalize(text)


def test_zone_abbreviations_override_built_in_names() -> None:
    normalizer: DatetimeNormalizer = DatetimeNormalizer(
        zone_abbreviations={
            "CST": ZoneInfo("Asia/Shanghai"),
            "PST": ZoneInfo("America/Los_Angeles"),
            "EST": timezone(timedelta(hours=10)),
            "現地時間": ZoneInfo("Asia/Bangkok"),
        }
    )

    assert normalizer.normalize("2024-01-05 13:05 CST").isoformat() == "2024-01-05T13:05+08:00"
    assert normalizer.normalize("2024-07-05 13:05 pst").isoformat() == "2024-07-05T13:05-07:00"
    assert normalizer.normalize("2024-01-05 13:05 EST").isoformat() == "2024-01-05T13:05+10:00"
    assert normalizer.normalize("2024年1月5日 現地時間13時").isoformat() == "2024-01-05T13+07:00"


def test_zone_abbreviations_apply_when_converting() -> None:
    normalizer: DatetimeNormalizer = DatetimeNormalizer(
        zone_abbreviations={"CST": ZoneInfo("Asia/Shanghai")}
    )
    moment: NormalizedDatetime = normalizer.normalize("2024-01-05 13:05 UTC")

    assert moment.to_time_zone("CST").isoformat() == "2024-01-05T21:05+08:00"
    assert moment.to_utc().to_time_zone("CST").isoformat() == "2024-01-05T21:05+08:00"
    assert normalizer.normalize("1704427200").to_time_zone("CST").isoformat() == (
        "2024-01-05T12:00:00+08:00"
    )
    assert NORMALIZER.normalize("2024-01-05 13:05 UTC").to_time_zone("CST").isoformat() == (
        "2024-01-05T07:05-06:00"
    )


def test_zone_abbreviations_must_be_readable_names() -> None:
    with pytest.raises(InvalidConfigurationError):
        _ = DatetimeNormalizer(zone_abbreviations={"my zone": UTC})


@pytest.mark.parametrize(
    ("text", "target", "expected"),
    [
        ("2024-01-05 13:05 JST", "UTC", "2024-01-05T04:05+00:00"),
        ("2024-01-05 13:05 JST", "America/New_York", "2024-01-04T23:05-05:00"),
        ("2024-07-05 13:05 JST", "America/New_York", "2024-07-05T00:05-04:00"),
        ("2024-01-05 13:05 UTC", "日本時間", "2024-01-05T22:05+09:00"),
        ("2024-01-05 13:05 UTC", "ロンドン時間", "2024-01-05T13:05+00:00"),
        ("2024-01-05 13:05 UTC", "+05:30", "2024-01-05T18:35+05:30"),
        ("2024-01-05 13:05 UTC", "ＪＳＴ", "2024-01-05T22:05+09:00"),
        # Across a transition, the fold of the result tells the two passes over 01:30 apart.
        ("2024-11-03 05:30Z", "America/New_York", "2024-11-03T01:30-04:00"),
        ("2024-11-03 06:30Z", "America/New_York", "2024-11-03T01:30-05:00"),
        # The precision grows only as far as the result needs.
        ("2024-01-05 13時 JST", "Asia/Tokyo", "2024-01-05T13+09:00"),
        ("2024-01-05 13時 JST", "Asia/Kolkata", "2024-01-05T09:30+05:30"),
        ("2024-01-05 13時 JST", "Asia/Kathmandu", "2024-01-05T09:45+05:45"),
        ("2024-01-05 13:05:09 JST", "UTC", "2024-01-05T04:05:09+00:00"),
        ("1800-01-01 00時 UTC", "Asia/Tokyo", "1800-01-01T09:18:59+09:18:59"),
    ],
)
def test_to_time_zone(text: str, target: str, expected: str) -> None:
    assert NORMALIZER.normalize(text).to_time_zone(target).isoformat() == expected


def test_to_time_zone_accepts_a_tzinfo() -> None:
    target: tzinfo = ZoneInfo("Asia/Tokyo")
    converted: NormalizedDatetime = NORMALIZER.normalize("2024-01-05 13:05Z").to_time_zone(target)

    assert converted.value.tzinfo is target
    assert converted.precision is DatetimePrecision.MINUTE


def test_to_utc() -> None:
    assert (
        NORMALIZER.normalize("2024年1月5日午前9時 JST").to_utc().isoformat()
        == "2024-01-05T00+00:00"
    )


@pytest.mark.parametrize("text", ["2024-01-05 13:05", "2024-01-05", "2024-01", "2024"])
def test_naive_value_cannot_be_converted(text: str) -> None:
    with pytest.raises(AmbiguousDatetimeError):
        _ = NORMALIZER.normalize(text).to_time_zone("JST")
    with pytest.raises(AmbiguousDatetimeError):
        _ = NORMALIZER.normalize(text).to_utc()


class _ZoneWithoutOffset(tzinfo):
    @override
    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        return None

    @override
    def dst(self, dt: datetime | None) -> timedelta | None:
        return None

    @override
    def tzname(self, dt: datetime | None) -> str | None:
        return None


def test_target_without_an_offset_is_rejected() -> None:
    with pytest.raises(InvalidDatetimeError):
        _ = NORMALIZER.normalize("2024-01-05 13:05Z").to_time_zone(_ZoneWithoutOffset())


@pytest.mark.parametrize(
    "text",
    [
        "2024-01-05 10:00-11:00",
        "2024/1/5 9:00-12:00",
        "2024/1/5 10:00ー11:00",
        "2024-01-05 10:00 -11:00",
        "2024-01-05 13:00-15:00",
        "2024-01-05 09-12",
        "2024-01-05 1000-1100",
        "2024年1月5日9時-12",
        "2024年1月5日午前9時半-11:00",
        "2024-01-05 10:00:00-11:00:00",
        # A date alone, where the number may also be the next day
        "2024-01-05-06",
        "2024-01-05 -05:00",
    ],
)
def test_text_that_may_be_a_range_is_rejected(text: str) -> None:
    with pytest.raises(AmbiguousDatetimeError):
        _ = NORMALIZER.normalize(text)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2024-01-05T10:00-11:00", "2024-01-05T10:00-11:00"),
        ("20240105T1000-1100", "2024-01-05T10:00-11:00"),
        ("2024-01-05 10:00:00-11:00", "2024-01-05T10:00:00-11:00"),
        ("2024-01-05 10:00:00-05", "2024-01-05T10:00:00-05:00"),
        ("2024-01-05 10:00:00.5-05:00", "2024-01-05T10:00:00.500000-05:00"),
        ("2024-01-05 10:00 UTC-11:00", "2024-01-05T10:00-11:00"),
        ("2024-01-05 10:00 GMT-5", "2024-01-05T10:00-05:00"),
        ("2024-01-05 10:00-11:00[Pacific/Pago_Pago]", "2024-01-05T10:00-11:00"),
        ("2024-01-05 10:00+11:00", "2024-01-05T10:00+11:00"),
    ],
)
def test_marked_negative_offsets_are_read(text: str, expected: str) -> None:
    assert NORMALIZER.normalize(text).isoformat() == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2024-01-05 JST", "2024-01-04T15+00:00"),
        ("2024-01-05 Asia/Tokyo", "2024-01-04T15+00:00"),
        ("2024-01-05+09:00", "2024-01-04T15+00:00"),
        ("2024-01-05 UTC-5", "2024-01-05T05+00:00"),
        ("2024-01-05Z", "2024-01-05T00+00:00"),
        ("2024年1月5日 日本時間", "2024-01-04T15+00:00"),
        ("2024年1月5日(日本時間)", "2024-01-04T15+00:00"),
        ("2024年1月5日(金)、日本時間", "2024-01-04T15+00:00"),
        ("January 5, 2024 JST", "2024-01-04T15+00:00"),
        ("2024-01-05-05:00[America/New_York]", "2024-01-05T05+00:00"),
    ],
)
def test_time_zone_after_a_date(text: str, expected: str) -> None:
    normalized: NormalizedDatetime = NORMALIZER.normalize(text)

    assert normalized.is_time_zone_stated
    assert normalized.precision is DatetimePrecision.DAY
    assert normalized.to_utc().isoformat() == expected


def test_time_zone_after_a_date_takes_precedence_over_the_default() -> None:
    assert NORMALIZER.normalize("2024-01-05 UTC", default_time_zone="JST").value == datetime(
        2024, 1, 5, tzinfo=UTC
    )


def test_date_moved_by_its_time_zones_shows_the_time() -> None:
    assert NORMALIZER.normalize("2024-01-05 +08:00[Asia/Tokyo]").isoformat() == (
        "2024-01-05T01+09:00"
    )


@pytest.mark.parametrize("text", ["2024 JST", "2024-01 JST", "2024年1月 日本時間", "2024-01+09:00"])
def test_time_zone_after_a_partial_date_is_rejected(text: str) -> None:
    with pytest.raises(UnrecognizedDatetimeError):
        _ = NORMALIZER.normalize(text)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2024年1月5日、午後1時", "2024-01-05T13"),
        ("2024年1月5日(金)、午後1時", "2024-01-05T13"),
        ("January 5, 2024、13:05", "2024-01-05T13:05"),
    ],
)
def test_japanese_comma_separates_a_date_from_a_time(text: str, expected: str) -> None:
    assert NORMALIZER.normalize(text).isoformat() == expected


def test_japanese_comma_does_not_hide_a_short_year() -> None:
    with pytest.raises(AmbiguousDatetimeError):
        _ = NORMALIZER.normalize("1月5日(金)、24", default_year=2024)


def test_long_run_of_spaces_is_handled_quickly() -> None:
    started: float = perf_counter()

    with pytest.raises(UnrecognizedDatetimeError):
        _ = NORMALIZER.normalize("2024" + " " * 200_000 + "x")

    assert perf_counter() - started < 5


@pytest.mark.parametrize(
    ("text", "error"),
    [
        ("Mars/Olympus", UnrecognizedDatetimeError),
        ("+25:00", InvalidDatetimeError),
    ],
)
def test_unusable_target_is_rejected(text: str, error: type[Exception]) -> None:
    with pytest.raises(error):
        _ = NORMALIZER.normalize("2024-01-05 13:05Z").to_time_zone(text)


@pytest.mark.parametrize(
    ("text", "target"),
    [
        ("0001-01-01 00:00 UTC", "-05:00"),
        ("0001-01-01 00:00 JST", "UTC"),
        ("9999-12-31 23:00 UTC", "Asia/Tokyo"),
        ("9999-12-31 23:00 EST", "UTC"),
    ],
)
def test_moment_out_of_range_is_rejected(text: str, target: str) -> None:
    with pytest.raises(InvalidDatetimeError):
        _ = NORMALIZER.normalize(text).to_time_zone(target)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2024-01-05 13:05", "2024-01-05T13:05+09:00"),
        ("2024年1月5日25時", "2024-01-06T01+09:00"),
        # A time zone in the text takes precedence.
        ("2024-01-05 13:05 UTC", "2024-01-05T13:05+00:00"),
        # The precision of a date is kept, while the value becomes aware.
        ("2024-01-05", "2024-01-05"),
        ("2024-01", "2024-01"),
    ],
)
def test_default_time_zone(text: str, expected: str) -> None:
    assert NORMALIZER.normalize(text, default_time_zone="Asia/Tokyo").isoformat() == expected


def test_default_time_zone_converts_a_date_from_its_zone() -> None:
    normalized: NormalizedDatetime = NORMALIZER.normalize("2024-01-05", default_time_zone="JST")

    assert normalized.is_time_zone_stated
    assert normalized.to_utc().isoformat() == "2024-01-04T15+00:00"


def test_default_time_zone_follows_daylight_saving_time() -> None:
    zone: ZoneInfo = ZoneInfo("America/New_York")

    assert NORMALIZER.normalize("2024-07-05 13:05", default_time_zone=zone).isoformat() == (
        "2024-07-05T13:05-04:00"
    )
    assert NORMALIZER.normalize("2024-03-10 02:30", default_time_zone=zone).isoformat() == (
        "2024-03-10T03:30-04:00"
    )
    assert NORMALIZER.normalize("2024-11-03 01:30", default_time_zone=zone).isoformat() == (
        "2024-11-03T01:30-04:00"
    )


def test_default_time_zone_is_validated_even_when_unused() -> None:
    with pytest.raises(UnrecognizedDatetimeError):
        _ = NORMALIZER.normalize("2024-01-05", default_time_zone="Mars/Olympus")


@given(
    st.datetimes(min_value=datetime(1950, 1, 1), max_value=datetime(2100, 12, 31)),
    st.sampled_from(ZONES),
    st.sampled_from(ZONES),
)
def test_conversion_keeps_the_moment_and_reads_back(
    moment: datetime, source: str, target: str
) -> None:
    original: NormalizedDatetime = NormalizedDatetime(
        value=moment.replace(tzinfo=UTC).astimezone(ZoneInfo(source)),
        precision=DatetimePrecision.MICROSECOND,
    )

    converted: NormalizedDatetime = original.to_time_zone(target)

    assert converted.value == original.value
    assert NORMALIZER.normalize(converted.isoformat()).value == converted.value


@given(st.dates(min_value=date(1950, 1, 1), max_value=date(2100, 12, 31)), st.times())
def test_offset_and_region_read_back_as_the_same_moment(day: date, wall_clock: time) -> None:
    moment: datetime = datetime.combine(day, wall_clock, UTC).astimezone(
        ZoneInfo("America/New_York")
    )

    assert NORMALIZER.normalize(f"{moment.isoformat()}[America/New_York]").value == moment
