# datetime_normalizer

## Overview

Public package of DatetimeNormalizer. The `DatetimeNormalizer` facade canonicalizes text, reads it, and returns a `NormalizedDatetime`.

## Components

| Component | Responsibility |
| --- | --- |
| [normalizer.py](normalizer.py) | `DatetimeNormalizer` facade that combines the readers |
| [normalized_datetime.py](normalized_datetime.py) | `NormalizedDatetime`: the moment, its precision, ISO 8601 output, and conversion between time zones |
| [precision.py](precision.py) | `DatetimePrecision`: smallest unit stated in the text, and how far a moved time refines it |
| [time_zone_localizer.py](time_zone_localizer.py) | `TimeZoneLocalizer`: attaches time zones to read values |
| [text/](text/README.md) | Removal of character-level differences before reading |
| [readers/](readers/README.md) | Reading of dates, times, time zones, Unix time, and weekdays |
| [results/](results/README.md) | Values the readers return |
| [notations/](notations/README.md) | Enums of the ways dates and times are written |
| [errors/](errors/README.md) | Exception hierarchy rooted at `DatetimeNormalizationError` |
