from datetime import date, datetime, time, timedelta, timezone

from hypothesis import given
from hypothesis import strategies as st

from datetime_normalizer import (
    DatetimeNormalizer,
    DatetimePrecision,
    JapaneseEra,
    NormalizedDatetime,
)

NORMALIZER: DatetimeNormalizer = DatetimeNormalizer()
OFFSETS: st.SearchStrategy[timezone | None] = st.none() | st.integers(
    min_value=-12 * 60, max_value=14 * 60
).map(lambda minutes: timezone(timedelta(minutes=minutes)))


@given(st.dates(), st.times(), OFFSETS)
def test_iso_output_reads_back_as_itself(day: date, moment: time, offset: timezone | None) -> None:
    normalized: NormalizedDatetime = NormalizedDatetime(
        value=datetime.combine(day, moment, offset),
        precision=DatetimePrecision.MICROSECOND,
    )

    assert NORMALIZER.normalize(normalized.isoformat()) == normalized


@given(st.dates(min_value=date(1873, 1, 1), max_value=date(2100, 12, 31)))
def test_era_notation_reads_as_the_same_day(day: date) -> None:
    era: JapaneseEra = next(era for era in reversed(JapaneseEra) if era.first_day <= day)
    text: str = f"{era.label}{day.year - era.first_year + 1}年{day.month}月{day.day}日"

    assert NORMALIZER.normalize(text).value.date() == day
