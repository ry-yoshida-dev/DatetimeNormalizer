# results

## Overview

Values the readers return, before the facade combines them into a `NormalizedDatetime`.

## Components

| Component | Responsibility |
| --- | --- |
| [date.py](date.py) | `DateResult`: the date and the text after it |
| [time.py](time.py) | `TimeResult`: the time and its time zones |
| [weekday.py](weekday.py) | `WeekdayResult`: the weekday and the remaining text |
