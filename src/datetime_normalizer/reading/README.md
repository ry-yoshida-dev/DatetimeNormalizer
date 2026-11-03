# reading

## Overview

Steps that turn text into validated date and time values. `TextCanonicalizer` removes
character-level differences, `WeekdayExtractor` takes out the weekday, `DateReader` reads the
date at the start, and `TimeReader` reads everything after it, using `TimeZoneReader` for time zones.
`TimeZoneLocalizer` then places the time in them. Readers match whole notations
with regular expressions, so text that fits no notation fails instead of being guessed at.

## Components

| Component | Responsibility |
| --- | --- |
| [text_canonicalizer.py](text_canonicalizer.py) | `TextCanonicalizer`: width, case, dashes, spacing, and numerals |
| [kanji_numeral_converter.py](kanji_numeral_converter.py) | `KanjiNumeralConverter`: positional and unit-based kanji numerals to digits |
| [weekday_extractor.py](weekday_extractor.py) | `WeekdayExtractor`: takes the Japanese or English weekday out of the text |
| [weekday_extraction.py](weekday_extraction.py) | `WeekdayExtraction`: the weekday and the remaining text |
| [date.py](date.py) | `DateReader`: date notations, calendar validation, and era ranges |
| [date_result.py](date_result.py) | `DateReading`: the date and the text after it |
| [time.py](time.py) | `TimeReader`: clock and Japanese time notations, and where time zones are written |
| [time_result.py](time_result.py) | `TimeReading`: the time and its time zones |
| [time_zone.py](time_zone.py) | `TimeZoneReader`: offsets, abbreviations, IANA names, and Japanese names |
| [time_zone_localizer.py](time_zone_localizer.py) | `TimeZoneLocalizer`: attaches time zones, settling times skipped or repeated by daylight saving time and zones that disagree |
| [unix_time.py](unix_time.py) | `UnixTimeReader`: seconds and milliseconds since 1970 |
| [japanese_era.py](japanese_era.py) | `JapaneseEra`: era names, year conversion, and first and last days |
| [meridiem.py](meridiem.py) | `Meridiem`: conversion from English and Japanese 12-hour clocks |
