# errors

## Overview

Exception hierarchy of DatetimeNormalizer. Every error derives from
`DatetimeNormalizationError`, which is a `ValueError`.

## Components

| Component | Responsibility |
| --- | --- |
| [base.py](base.py) | `DatetimeNormalizationError`: base of all library errors |
| [unrecognized.py](unrecognized.py) | `UnrecognizedDatetimeError`: the text follows no supported notation |
| [ambiguous.py](ambiguous.py) | `AmbiguousDatetimeError`: the text has several plausible readings, or a naive value is converted |
| [configuration.py](configuration.py) | `InvalidConfigurationError`: an argument that configures the normalizer cannot be used |
| [invalid.py](invalid.py) | `InvalidDatetimeError`: the date or time cannot exist, e.g. February 30, a day outside its era, or a wrong weekday |
