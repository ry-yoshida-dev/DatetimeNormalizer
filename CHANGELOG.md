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
