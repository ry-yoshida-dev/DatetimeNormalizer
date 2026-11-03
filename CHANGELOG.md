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

### Changed

- Time zone ambiguities no longer raise. Shared abbreviations such as `CST` mean the most common
  zone, times skipped by daylight saving time move ahead, repeated ones are the earlier one, zones
  that disagree are a conversion, and naive values convert from UTC.
