# Changelog

All notable changes are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/); before 1.0.0, a minor version may break
the API.

## [Unreleased]

### Added

- `DatetimeNormalizer` reads numeric, Japanese, era, and English dates with optional times
  and time zones, and returns a `NormalizedDatetime` that keeps the precision of the text.
- `normalize(text, default_year=...)` reads dates without a year, such as `1月5日`.
- `NormalizedDatetime.to_time_zone` and `to_utc` convert a moment between time zones.
- `normalize(text, default_time_zone=...)` places times that do not state a time zone.
- Time zones can be written as IANA names, more abbreviations, Japanese names, offsets with
  seconds, notes such as `+09:00[Asia/Tokyo]`, and before the time as in `日本時間午後1時`.
- `DatetimeNormalizer(zone_abbreviations=...)` overrides the readings of time zone names.
- Unix time in seconds and milliseconds is read as UTC.
- A time zone can follow a date directly, as in `2024-01-05 JST`, and `、` separates a date from
  a time.

### Changed

- Time zone ambiguities no longer raise. Shared abbreviations such as `CST` mean the most common
  zone, times skipped by daylight saving time move ahead, repeated ones are the earlier one, and
  zones that disagree are a conversion.
- Converting a naive value raises `AmbiguousDatetimeError` instead of assuming UTC.
- A negative offset that may be the end of a range, as in `10:00-11:00`, raises
  `AmbiguousDatetimeError`. A `T`, seconds, a prefix, or a note marks it as an offset.
- An unusable key of `zone_abbreviations` raises `InvalidConfigurationError`.
- `NormalizedDatetime.is_timezone_aware` is renamed to `is_time_zone_stated`.
- `datetime_normalizer.reading` is split into `readers`, `results`, `text`, and `notations`, and
  `datetime_normalizer.result` is renamed to `normalized_datetime`. Imports from
  `datetime_normalizer` itself are unchanged.

### Fixed

- `to_time_zone` and `to_utc` read names with the `zone_abbreviations` of the normalizer.
- A long run of spaces no longer makes normalizing take quadratic time.
- `to_time_zone` raises `InvalidDatetimeError` for a `tzinfo` without an offset.
- `Japan` is read on systems whose time zone database leaves out old IANA names.
- A `default_year` out of range raises `InvalidDatetimeError` even when the text states a year.
