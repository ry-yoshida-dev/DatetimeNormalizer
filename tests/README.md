# tests

## Overview

Pytest suite. Notations and rejection rules are tested through the `DatetimeNormalizer` facade.

## Components

| Component | Responsibility |
| --- | --- |
| [test_datetime_normalizer.py](test_datetime_normalizer.py) | Accepted notations, precision, time zones, and each kind of rejection |
| [test_round_trip.py](test_round_trip.py) | Property-based round trip of ISO output and era notation |
| [reading/](reading/README.md) | Unit tests of the reading steps |
