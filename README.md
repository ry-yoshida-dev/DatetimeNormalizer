# DatetimeNormalizer

## Overview

DatetimeNormalizer reads date and time text in the many ways it is written, including Japanese
notation, and returns one canonical value. It has no runtime dependencies and needs Python 3.12+.

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
```

### Principles

- **Never guess.** Text with several plausible readings raises an error, because a wrong guess
  silently corrupts data while an error can be handled.
- **Keep the precision.** `2024年1月` stays a month: `isoformat()` gives `2024-01`, and
  `precision` tells what `value` can be trusted for.
- **Do not invent a time zone.** The result is naive unless the text states a zone.

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
| Time zone | `Z`, `+09:00`, `+0900`, `+9`, `UTC+9`, `UTC`, `GMT`, `JST`, `日本時間` |

A time needs a full date. An hour from 24 to 47 belongs to the next day (`24:00`, `25時`).
A fraction of a second beyond microseconds is truncated.

## Errors

Every error derives from `DatetimeNormalizationError`, which is a `ValueError`.

| Error | Raised for |
| --- | --- |
| `UnrecognizedDatetimeError` | No supported notation: `昨日`, `13:05`, `2024-01-05 13:05 EST` |
| `AmbiguousDatetimeError` | Several readings: `1/2/2024` without `date_order`, `1月5日` without `default_year`, `24/1/5`, `24年1月5日`, `午後12時` |
| `InvalidDatetimeError` | Cannot exist: `2023-02-29`, `平成31年5月1日`, `明治5年12月31日`, `2024年1月5日(月)`, `13:00-15:00` |

Some of these rules are less obvious:

- **Year-last dates** always need `date_order`, even `13/1/2024`. Inferring the order per value
  would read one column in two different orders.
- **`午前12時` and `午後12時`** are rejected. 午後12時 is midnight by the original definition and
  noon in common use. `12:30 PM` and `正午` are accepted, as they have one reading.
- **Time zone abbreviations** other than UTC, GMT, and JST are rejected, because many, such as
  `CST` and `IST`, are shared by several zones.
- **Meiji 1 to 5** are rejected. Those dates are on the lunisolar calendar, which cannot be
  converted by arithmetic.
- **Time zone offsets** outside -12:00 to +14:00 are rejected, which catches ranges such as
  `13:00-15:00`. A range within them, such as `09:00-12:00`, cannot be told from a negative
  offset and is read as one, so split ranges before normalizing.
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
uv run ruff check . && uv run ruff format --check .
uv run mypy src tests
uv run basedpyright
```
