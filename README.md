# DatetimeNormalizer

## Overview

DatetimeNormalizer reads date and time text in the many ways it is written, including Japanese
notation, and returns one canonical value, which can then be converted between time zones. It
never guesses: text with several plausible readings raises an error, the stated precision is kept,
and no time zone is invented. It has no runtime dependencies and needs Python 3.12+.

See [docs/reference.md](docs/reference.md) for the supported notations and time zone abbreviations.

## Installation

```toml
[project]
dependencies = [
    "datetime-normalizer @ git+https://github.com/ry-yoshida-dev/DatetimeNormalizer.git@<commit>",
]
```

## Usage

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

## Development

Doctests are not part of the default test paths:

```bash
uv run pytest --doctest-modules src
```
