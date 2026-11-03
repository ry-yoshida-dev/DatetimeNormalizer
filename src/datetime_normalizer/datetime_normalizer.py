from datetime import date, datetime, timedelta

from datetime_normalizer.date_order import DateOrder
from datetime_normalizer.datetime_precision import DatetimePrecision
from datetime_normalizer.errors import InvalidDatetimeError, UnrecognizedDatetimeError
from datetime_normalizer.normalized_datetime import NormalizedDatetime
from datetime_normalizer.reading import (
    DateReader,
    DateReading,
    TextCanonicalizer,
    TimeReader,
    TimeReading,
    WeekdayExtraction,
    WeekdayExtractor,
)


class DatetimeNormalizer:
    """
    Normalizer of free-form date and time text, including Japanese notation.

    Text with several plausible readings is rejected instead of guessed at, so that a batch of
    records is not silently corrupted. The result keeps the precision of the text, and stays
    naive unless the text states a time zone.

    Parameters
    ----------
    date_order : DateOrder | None
        Order of the month and day in dates written with the year last, such as ``1/2/2024``.
        With ``None``, those dates raise ``AmbiguousDatetimeError``.

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
    """

    def __init__(self, date_order: DateOrder | None = None) -> None:
        self._date_reader: DateReader = DateReader(date_order)

    def normalize(self, text: str, *, default_year: int | None = None) -> NormalizedDatetime:
        """
        Normalize one date and time.

        Parameters
        ----------
        text : str
            A date, optionally followed by a time and time zone.
        default_year : int | None
            Year of a date that does not state one, such as ``1月5日``. A year in the text takes
            precedence. With ``None``, those dates raise ``AmbiguousDatetimeError``.

        Returns
        -------
        NormalizedDatetime
            The moment and the precision of the text.

        Raises
        ------
        UnrecognizedDatetimeError
            If the text follows no supported notation, including a time without a full date.
        AmbiguousDatetimeError
            If the text has several plausible readings.
        InvalidDatetimeError
            If the date or time cannot exist, or the stated weekday contradicts the date.
        """
        extraction: WeekdayExtraction = WeekdayExtractor.extract(
            TextCanonicalizer.canonicalize(text)
        )
        date_reading: DateReading = self._date_reader.read(extraction.text, default_year)
        time_reading: TimeReading | None = (
            TimeReader.read(date_reading.rest) if date_reading.rest else None
        )

        if time_reading is not None and date_reading.day is None:
            raise UnrecognizedDatetimeError(f"A time needs a full date: {text}")
        calendar_day: date = date(date_reading.year, date_reading.month or 1, date_reading.day or 1)
        if extraction.weekday is not None:
            if date_reading.day is None:
                raise UnrecognizedDatetimeError(f"A weekday needs a full date: {text}")
            if calendar_day.weekday() != extraction.weekday:
                raise InvalidDatetimeError(
                    f"{calendar_day} is not a {extraction.weekday.name.lower()}: {text}"
                )
        return NormalizedDatetime(
            value=self._to_datetime(calendar_day, time_reading, text),
            precision=self._to_precision(date_reading, time_reading),
        )

    @staticmethod
    def _to_datetime(calendar_day: date, time_reading: TimeReading | None, text: str) -> datetime:
        if time_reading is None:
            return datetime.combine(calendar_day, datetime.min.time())
        days_carried, hour = divmod(time_reading.hour, 24)
        # An hour past midnight is on the next day, as in 24:00 and 25時.
        if days_carried > 0 and calendar_day == date.max:
            raise InvalidDatetimeError(f"Moment out of range: {text}")
        return datetime(
            calendar_day.year,
            calendar_day.month,
            calendar_day.day,
            hour,
            time_reading.minute or 0,
            time_reading.second or 0,
            time_reading.microsecond or 0,
            time_reading.time_zone,
        ) + timedelta(days=days_carried)

    @staticmethod
    def _to_precision(
        date_reading: DateReading, time_reading: TimeReading | None
    ) -> DatetimePrecision:
        if time_reading is None:
            if date_reading.month is None:
                return DatetimePrecision.YEAR
            return DatetimePrecision.MONTH if date_reading.day is None else DatetimePrecision.DAY
        if time_reading.microsecond is not None:
            return DatetimePrecision.MICROSECOND
        if time_reading.second is not None:
            return DatetimePrecision.SECOND
        return DatetimePrecision.HOUR if time_reading.minute is None else DatetimePrecision.MINUTE
