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
| [date_reader.py](date_reader.py) | `DateReader`: date notations, calendar validation, and era ranges |
| [date.py](date.py) | `DateReading`: the date and the text after it |
| [time_reader.py](time_reader.py) | `TimeReader`: clock and Japanese time notations, and where time zones are written |
| [time.py](time.py) | `TimeReading`: the time and its time zones |
| [time_zone_reader.py](time_zone_reader.py) | `TimeZoneReader`: offsets, abbreviations, IANA names, and Japanese names |
| [time_zone_localizer.py](time_zone_localizer.py) | `TimeZoneLocalizer`: attaches time zones, settling times skipped or repeated by daylight saving time and zones that disagree |
| [unix_time_reader.py](unix_time_reader.py) | `UnixTimeReader`: seconds and milliseconds since 1970 |
| [japanese_era.py](japanese_era.py) | `JapaneseEra`: era names, year conversion, and first and last days |
| [meridiem.py](meridiem.py) | `Meridiem`: conversion from English and Japanese 12-hour clocks |
