# datetime_normalizer

## Overview

Public package of DatetimeNormalizer. `DatetimeNormalizer` is the facade: it canonicalizes text
with `text/`, reads it with `readers/`, and returns a `NormalizedDatetime`.

## Components

| Component | Responsibility |
| --- | --- |
| [normalizer.py](normalizer.py) | `DatetimeNormalizer` facade: combines the readers, verifies the weekday, carries late hours to the next day, and places the time in its time zone |
| [normalized_datetime.py](normalized_datetime.py) | `NormalizedDatetime`: the moment, its precision, ISO 8601 output, and conversion between time zones |
| [precision.py](precision.py) | `DatetimePrecision`: smallest unit stated in the text, and how far a moved time refines it |
| [time_zone_localizer.py](time_zone_localizer.py) | `TimeZoneLocalizer`: attaches time zones, settling times skipped or repeated by daylight saving time and zones that disagree |
| [text/](text/README.md) | Removal of character-level differences before reading |
| [readers/](readers/README.md) | Reading of dates, times, time zones, Unix time, and weekdays |
| [results/](results/README.md) | Values the readers return |
| [notations/](notations/README.md) | Enums of the ways dates and times are written |
| [errors/](errors/README.md) | Exception hierarchy rooted at `DatetimeNormalizationError` |
