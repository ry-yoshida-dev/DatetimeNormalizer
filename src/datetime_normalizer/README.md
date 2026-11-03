# datetime_normalizer

## Overview

Public package of DatetimeNormalizer. `DatetimeNormalizer` is the facade that reads text with
`reading/` and returns a `NormalizedDatetime`.

## Components

| Component | Responsibility |
| --- | --- |
| [datetime_normalizer.py](datetime_normalizer.py) | `DatetimeNormalizer` facade: combines the readers, verifies the weekday, and carries late hours to the next day |
| [normalized_datetime.py](normalized_datetime.py) | `NormalizedDatetime`: the moment, its precision, and ISO 8601 output |
| [datetime_precision.py](datetime_precision.py) | `DatetimePrecision`: smallest unit stated in the text |
| [date_order.py](date_order.py) | `DateOrder`: order of month and day in dates written with the year last |
| [reading/](reading/README.md) | Canonicalization of characters and reading of dates, times, weekdays, and eras |
| [errors/](errors/README.md) | Exception hierarchy rooted at `DatetimeNormalizationError` |
