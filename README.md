# DatetimeNormalizer

## Overview

DatetimeNormalizer reads date and time text in the many ways it is written, including Japanese
notation, and returns one canonical value, which can then be converted between time zones. It has
no runtime dependencies and needs Python 3.12+.

```python
from datetime_normalizer import DatetimeNormalizer

normalizer = DatetimeNormalizer()

normalizer.normalize("令和６年１月５日（金）午後１時半").isoformat()  # '2024-01-05T13:30'
normalizer.normalize("平成三十一年四月").isoformat()  # '2019-04'
normalizer.normalize("2024:01:05 13:05:00+09:00").isoformat()  # '2024-01-05T13:05:00+09:00'
normalizer.normalize("1月5日", default_year=2024).isoformat()  # '2024-01-05'

result = normalizer.normalize("2024/1/5 25時")
result.value  # datetime(2024, 1, 6, 1, 0)
result.precision  # DatetimePrecision.HOUR

tokyo = normalizer.normalize("2024年7月5日午後1時 日本時間")
tokyo.to_utc().isoformat()  # '2024-07-05T04+00:00'
tokyo.to_time_zone("America/New_York").isoformat()  # '2024-07-05T00-04:00'
tokyo.to_time_zone("インド標準時").isoformat()  # '2024-07-05T09:30+05:30'

normalizer.normalize("2024-01-05 13:05", default_time_zone="Asia/Tokyo").isoformat()
# '2024-01-05T13:05+09:00'
```

### Principles

- **Never guess at a date.** Text with several plausible readings raises an error, because a
  wrong guess silently corrupts data while an error can be handled.
- **Always read a stated time zone.** The ambiguities of its name have fixed readings, listed
  under [Time zones](#time-zones), so a batch does not stop on them. Check those readings against
  your data.
- **Keep the precision.** `2024年1月` stays a month: `isoformat()` gives `2024-01`, and
  `precision` tells what `value` can be trusted for.
- **Do not invent a time zone.** The result is naive unless the text states a zone or the caller
  passes `default_time_zone`, and a naive result cannot be converted.

## Setup

```toml
[project]
dependencies = [
    "datetime-normalizer @ git+https://github.com/ry-yoshida-dev/DatetimeNormalizer.git@<commit>",
]
```

## Supported notations

Full-width characters, kanji numerals, spacing around units, and letter case are folded first.

| Kind | Examples |
| --- | --- |
| Numeric date | `2024-01-05`, `2024/1/5`, `2024.1.5`, `2024:01:05`, `20240105` |
| Partial date | `2024`, `2024-01`, `2024年`, `2024年1月`, `January 2024` |
| Japanese date | `2024年1月5日`, `二〇二四年一月五日`, `二千二十四年十二月三十一日` |
| Era | `令和6年1月5日`, `令和元年5月1日`, `R6.1.5`, `H31/4/30`, `令6.1.5`, `㋿6年1月5日` |
| English date | `January 5, 2024`, `5 Jan 2024`, `05-Sept-2024` |
| Year-last date | `1/2/2024`, with `date_order` set |
| Date without a year | `1月5日`, `1月`, `January 5`, `5 Jan`, with `default_year` set; `1/5`, with `date_order` also set |
| Weekday | `(金)`, `（金曜日）`, `金曜`, `Friday,`, `(Fri)`; verified against the date, then dropped |
| Time | `13`, `13:05`, `13:05:09.5`, `130509`, `13時5分9秒`, `1時半`, `正午` |
| 12-hour clock | `午後1時`, `午前9:30`, `1:30 PM`, `1 p.m.` |
| Offset | `Z`, `+09:00`, `+0900`, `+9`, `UTC+9`, `GMT-05:00`, `+09:18:59` |
| IANA time zone | `Asia/Tokyo`, `america/new_york`, `Etc/GMT+9`, `Japan` |
| Abbreviation | `UTC`, `GMT`, `JST`, `KST`, `HKT`, `SGT`, `EST`, `EDT`, `PDT`, `CET`, `CEST`, `AEST`, `NZST`, and others in [time_zone.py](src/datetime_normalizer/reading/time_zone.py); `ET`, `CT`, `MT`, `PT` |
| Japanese time zone | `日本時間`, `日本標準時`, `協定世界時`, `世界標準時`, `世界時`, `世界時間`, `グリニッジ標準時`, `東部標準時`, `米国東部時間`, `ロンドン時間`, `シンガポール時間` |
| Zone before the time | `日本時間午後1時`, `(日本時間)13:05`, `UTC 13:05` |
| Unix time | `1704427200`, `1704427200.5`, `1704427200000` (milliseconds); always UTC |
| Zone as a note | `+09:00[Asia/Tokyo]`, `+0900 (JST)`, `GMT+0900 (日本標準時)`, `13時(日本時間)` |
| Zone after a date | `2024-01-05 JST`, `2024-01-05+09:00`, `2024-01-05Z`, `2024年1月5日(日本時間)` |

A time or a zone needs a full date. An hour from 24 to 47 belongs to the next day (`24:00`, `25時`).
A fraction of a second beyond microseconds is truncated.

## Time zones

| API | Description |
| --- | --- |
| `result.to_time_zone(zone)` | The same moment in `zone`, a `tzinfo` or text in any notation above, read with the `zone_abbreviations` of the normalizer |
| `result.to_utc()` | The same moment in UTC |
| `normalize(text, default_time_zone=zone)` | The zone of a text that does not state one |
| `DatetimeNormalizer(zone_abbreviations={...})` | Readings of names, which override the built-in ones |

Offsets and abbreviations need nothing else. IANA names and names of regions read the time zone
database of the system. Where there is none, as on Windows and in slim containers, install
[`tzdata`](https://pypi.org/project/tzdata/); without it those names are rejected as unknown.

- **Abbreviations are fixed offsets**, as written: `EST` is -05:00 even in July. Names of regions
  follow daylight saving time: `America/New_York`, `ET`, and `米国東部時間` are -04:00 in July.
- **Shared abbreviations** mean the most common zone. To read a data set differently, pass
  `zone_abbreviations={"CST": ZoneInfo("Asia/Shanghai")}`.

  | Name | Read as | Also used for |
  | --- | --- | --- |
  | `CST`, `CDT` | United States Central, -06:00, -05:00 | China, Cuba |
  | `PST` | United States Pacific, -08:00 | Philippines |
  | `MST` | United States Mountain, -07:00 | Malaysia |
  | `AST`, `ADT` | Atlantic, -04:00, -03:00 | Arabia |
  | `IST` | India, +05:30 | Israel, Ireland |
  | `BST` | British Summer Time, +01:00 | Bangladesh |
  | `GST` | Gulf, +04:00 | South Georgia |
  | `AMT` | Amazon, -04:00 | Armenia |
  | `BDT` | Bangladesh, +06:00 | Brunei |
  | `ECT` | Ecuador, -05:00 | Eastern Caribbean |
  | `SST` | Samoa, -11:00 | Singapore |
  | `WST` | West Samoa, +13:00 | Western Australia |

- **A time skipped by daylight saving time** moves ahead by the skip: `2024-03-10 02:30` in New
  York is `03:30-04:00`. **A time repeated** is the earlier one: `2024-11-03 01:30` there is
  `-04:00`. An offset selects the later one: `2024-11-03 01:30-05:00[America/New_York]`.
- **Several zones in one text** that disagree are a conversion from the first to the last:
  `13:05+08:00[Asia/Tokyo]` is `14:05+09:00`, and `13:05Z[Asia/Tokyo]` is `22:05+09:00`.
- **A naive value cannot be converted**, as it is not a moment yet: `to_time_zone` and `to_utc`
  raise `AmbiguousDatetimeError`. Pass `default_time_zone`, which also applies to a date without
  a time, which then means midnight in that zone.
- **A date with a zone** means midnight in that zone, like one with `default_time_zone`, and
  keeps the precision of a day until it is converted.
- **The precision grows when a time moves**: `13時` in JST is `09:30` in India, not `09`. A date
  without a time gets an hour when converted.
- **`世界時` and `世界時間`** are read as UTC. Strictly, 世界時 is UT1, up to 0.9 seconds away.
- **Unix time** is read for 10 digits from `10` to `18`, which covers 2001 to 2030, and for any 13
  digits. Other numbers stay dates: `1999123113` is `1999-12-31T13`.
- **Out of range:** a moment that a conversion would move before year 1 or after year 9999 still
  raises `InvalidDatetimeError`, as does an unknown name or an offset that cannot exist.

## Errors

Every error derives from `DatetimeNormalizationError`, which is a `ValueError`.

| Error | Raised for |
| --- | --- |
| `UnrecognizedDatetimeError` | No supported notation: `昨日`, `13:05`, `2024-01-05 13:05 Mars/Olympus` |
| `AmbiguousDatetimeError` | Several readings: `1/2/2024` without `date_order`, `1月5日` without `default_year`, `24/1/5`, `24年1月5日`, `午後12時`, `2024-01-05 10:00-11:00`; or converting a naive value |
| `InvalidDatetimeError` | Cannot exist: `2023-02-29`, `平成31年5月1日`, `明治5年12月31日`, `2024年1月5日(月)`, `13:05+25:00` |
| `InvalidConfigurationError` | An argument of `DatetimeNormalizer` cannot be used: `zone_abbreviations={"my zone": UTC}` |

Some of these rules are less obvious:

- **Year-last dates** always need `date_order`, even `13/1/2024`. Inferring the order per value
  would read one column in two different orders.
- **`午前12時` and `午後12時`** are rejected. 午後12時 is midnight by the original definition and
  noon in common use. `12:30 PM` and `正午` are accepted, as they have one reading.
- **Meiji 1 to 5** are rejected. Those dates are on the lunisolar calendar, which cannot be
  converted by arithmetic.
- **Negative offsets** look like the end of a range, so `10:00-11:00` is rejected. Show that it
  is an offset with a `T` (`2024-01-05T10:00-11:00`), seconds on the time
  (`2024-01-05 10:00:00-11:00`), a prefix (`10:00 UTC-11:00`), or a note
  (`10:00-11:00[Pacific/Pago_Pago]`). Offsets outside -12:00 to +14:00 are always rejected.
- **Two 12-hour markers**, as in `午前1:30 PM`, are rejected, even when they agree.
- **`default_year`** is only used when the text states no year, and the date is validated in
  that year: `2月29日` needs a leap year, and `1月5日(月)` must fall on a Monday in it. The year
  is not inferred from the date or the current time.
- **A lone number after a date without a year** is rejected, as in `5 Jan 24` and `5 Jan 24 JST`, where 24 may be
  a short year rather than an hour. Write the hour with a unit or minutes: `5 Jan 24:00`.
- **Slash dates without a year** are the only numeric form accepted, because `1-5` and `1.5` are
  more often a range and a decimal.

Relative text such as `昨日` is not supported.

## Components

| Component | Description |
| --- | --- |
| [src/datetime_normalizer/](src/datetime_normalizer/README.md) | The library |
| [tests/](tests/README.md) | Pytest suite |
| [CHANGELOG.md](CHANGELOG.md) | Notable changes |

## Development

```bash
uv sync
uv run pytest
uv run pytest --doctest-modules src
uv run ruff check . && uv run ruff format --check .
uv run mypy src tests
uv run basedpyright
```
