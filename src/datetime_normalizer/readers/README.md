# readers

## Overview

Readers of canonical text: the weekday, the date at the start, and the time and time zones after it.

## Components

| Component | Responsibility |
| --- | --- |
| [date.py](date.py) | `DateReader`: date notations, calendar validation, and era ranges |
| [time.py](time.py) | `TimeReader`: clock and Japanese time notations, and where time zones are written |
| [time_zone.py](time_zone.py) | `TimeZoneReader`: offsets, abbreviations, IANA names, and Japanese names |
| [unix_time.py](unix_time.py) | `UnixTimeReader`: seconds and milliseconds since 1970 |
| [weekday.py](weekday.py) | `WeekdayReader`: takes the Japanese or English weekday out of the text |
