# datetime_normalizer

## Overview

Public package of DatetimeNormalizer. `DatetimeNormalizer` is the facade that reads text with
`reading/` and returns a `NormalizedDatetime`.

## Components

| Component | Responsibility |
| --- | --- |
| [normalizer.py](normalizer.py) | `DatetimeNormalizer` facade: combines the readers, verifies the weekday, carries late hours to the next day, and places the time in its time zone |
| [result.py](result.py) | `NormalizedDatetime`: the moment, its precision, ISO 8601 output, and conversion between time zones |
| [precision.py](precision.py) | `DatetimePrecision`: smallest unit stated in the text, and how far a moved time refines it |
| [date_order.py](date_order.py) | `DateOrder`: order of month and day in dates written with the year last |
| [reading/](reading/README.md) | Canonicalization of characters and reading of dates, times, weekdays, and eras |
| [errors/](errors/README.md) | Exception hierarchy rooted at `DatetimeNormalizationError` |
