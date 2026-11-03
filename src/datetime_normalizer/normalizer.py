from collections.abc import Mapping
from datetime import date, datetime, timedelta, tzinfo

from datetime_normalizer.errors import InvalidDatetimeError, UnrecognizedDatetimeError
from datetime_normalizer.normalized_datetime import NormalizedDatetime
from datetime_normalizer.notations import DateOrder
from datetime_normalizer.precision import DatetimePrecision
from datetime_normalizer.readers import (
    DateReader,
    TimeReader,
    TimeZoneReader,
    UnixTimeReader,
    WeekdayReader,
)
from datetime_normalizer.results import DateResult, TimeResult, WeekdayResult
from datetime_normalizer.text import TextCanonicalizer
from datetime_normalizer.time_zone_localizer import TimeZoneLocalizer


class DatetimeNormalizer:
    """
    Normalizer of free-form date and time text, including Japanese notation.

    Text with several plausible readings is rejected instead of guessed at, so that a batch of
    records is not silently corrupted. Time zones are the exception: their ambiguities have fixed
    readings, described in ``TimeZoneReader`` and ``TimeZoneLocalizer``. The result keeps the
    precision of the text, and stays naive unless the text or the caller states a time zone.

    Parameters
    ----------
    date_order : DateOrder | None
        Order of the month and day in dates written with the year last, such as ``1/2/2024``.
        With ``None``, those dates raise ``AmbiguousDatetimeError``.
    zone_abbreviations : Mapping[str, tzinfo] | None
        Readings of time zone names, such as ``{"CST": ZoneInfo("Asia/Shanghai")}``. They take
        precedence over the built-in names.

    Raises
    ------
    InvalidConfigurationError
        If a key of ``zone_abbreviations`` cannot appear in text as a time zone name.

    Examples
    --------
    >>> normalizer = DatetimeNormalizer()
    >>> normalizer.normalize("令和６年１月５日（金）午後１時半").isoformat()
    '2024-01-05T13:30'
    >>> normalizer.normalize("平成三十一年四月").isoformat()
    '2019-04'
    >>> normalizer.normalize("2024:01:05 13:05:00+09:00").isoformat()
    '2024-01-05T13:05:00+09:00'
    >>> normalizer.normalize("1月5日(金)", default_year=2024).isoformat()
    '2024-01-05'
    >>> normalizer.normalize("2024-01-05 13:05 America/New_York").to_utc().isoformat()
    '2024-01-05T18:05+00:00'
    """

    def __init__(
        self,
        date_order: DateOrder | None = None,
        zone_abbreviations: Mapping[str, tzinfo] | None = None,
    ) -> None:
        self._date_reader: DateReader = DateReader(date_order)
        self._time_zone_reader: TimeZoneReader = TimeZoneReader(zone_abbreviations)
        self._time_reader: TimeReader = TimeReader(self._time_zone_reader)

    def normalize(
        self,
        text: str,
        *,
        default_year: int | None = None,
        default_time_zone: tzinfo | str | None = None,
    ) -> NormalizedDatetime:
        """
        Normalize one date and time.

        Parameters
        ----------
        text : str
            A date, optionally followed by a time, a time zone, or both.
        default_year : int | None
            Year of a date that does not state one, such as ``1月5日``. A year in the text takes
            precedence. With ``None``, those dates raise ``AmbiguousDatetimeError``.
        default_time_zone : tzinfo | str | None
            Time zone of a text that does not state one. A time zone in the text takes
            precedence.

        Returns
        -------
        NormalizedDatetime
            The moment and the precision of the text.

        Raises
        ------
        UnrecognizedDatetimeError
            If the text follows no supported notation, including a time or a time zone without
            a full date.
        AmbiguousDatetimeError
            If the text has several plausible readings.
        InvalidDatetimeError
            If ``default_year`` is out of the range of ``datetime``, the date or time cannot exist,
            or the stated weekday contradicts the date.
        """
        if default_year is not None and not date.min.year <= default_year <= date.max.year:
            raise InvalidDatetimeError(f"Default year out of range: {default_year}")
        fallback_time_zone: tzinfo | None = (
            None if default_time_zone is None else self._time_zone_reader.resolve(default_time_zone)
        )
        canonical_text: str = TextCanonicalizer.canonicalize(text)
        unix_time: datetime | None = UnixTimeReader.read(canonical_text)
        if unix_time is not None:
            return NormalizedDatetime(
                value=unix_time,
                precision=DatetimePrecision.SECOND.refined_for(unix_time),
                time_zone_reader=self._time_zone_reader,
            )
        weekday_result: WeekdayResult = WeekdayReader.read(canonical_text)
        date_result: DateResult = self._date_reader.read(weekday_result.text, default_year)
        date_time_zones: tuple[tzinfo, ...] = self._time_reader.read_time_zones(date_result.rest)
        time_result: TimeResult | None = (
            self._time_reader.read(date_result.rest)
            if date_result.rest and not date_time_zones
            else None
        )

        if date_result.day is None and (time_result is not None or date_time_zones):
            raise UnrecognizedDatetimeError(f"A time or time zone needs a full date: {text}")
        calendar_day: date = date(date_result.year, date_result.month or 1, date_result.day or 1)
        if weekday_result.weekday is not None:
            if date_result.day is None:
                raise UnrecognizedDatetimeError(f"A weekday needs a full date: {text}")
            if calendar_day.weekday() != weekday_result.weekday:
                raise InvalidDatetimeError(
                    f"{calendar_day} is not a {weekday_result.weekday.name.lower()}: {text}"
                )
        stated_time_zones: tuple[tzinfo, ...] = (
            date_time_zones if time_result is None else time_result.time_zones
        )
        value: datetime = self._to_datetime(
            calendar_day,
            time_result,
            stated_time_zones or (() if fallback_time_zone is None else (fallback_time_zone,)),
            text,
        )
        precision: DatetimePrecision = self._to_precision(date_result, time_result)
        # A time moved by its time zone may need units the text did not state.
        is_moved: bool = time_result is not None or value.time() != datetime.min.time()
        return NormalizedDatetime(
            value=value,
            precision=precision.refined_for(value) if is_moved else precision,
            time_zone_reader=self._time_zone_reader,
        )

    @staticmethod
    def _to_datetime(
        calendar_day: date,
        time_result: TimeResult | None,
        time_zones: tuple[tzinfo, ...],
        text: str,
    ) -> datetime:
        if time_result is None:
            return TimeZoneLocalizer.localize(
                datetime.combine(calendar_day, datetime.min.time()), time_zones
            )
        days_carried, hour = divmod(time_result.hour, 24)
        # An hour past midnight is on the next day, as in 24:00 and 25時.
        if days_carried > 0 and calendar_day == date.max:
            raise InvalidDatetimeError(f"Moment out of range: {text}")
        wall_clock: datetime = datetime(
            calendar_day.year,
            calendar_day.month,
            calendar_day.day,
            hour,
            time_result.minute or 0,
            time_result.second or 0,
            time_result.microsecond or 0,
        ) + timedelta(days=days_carried)
        return TimeZoneLocalizer.localize(wall_clock, time_zones)

    @staticmethod
    def _to_precision(date_result: DateResult, time_result: TimeResult | None) -> DatetimePrecision:
        if time_result is None:
            if date_result.month is None:
                return DatetimePrecision.YEAR
            return DatetimePrecision.MONTH if date_result.day is None else DatetimePrecision.DAY
        if time_result.microsecond is not None:
            return DatetimePrecision.MICROSECOND
        if time_result.second is not None:
            return DatetimePrecision.SECOND
        return DatetimePrecision.HOUR if time_result.minute is None else DatetimePrecision.MINUTE
