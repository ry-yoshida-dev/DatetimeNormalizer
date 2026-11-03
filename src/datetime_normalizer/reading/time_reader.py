import re
from typing import ClassVar

from datetime_normalizer.errors import InvalidDatetimeError, UnrecognizedDatetimeError
from datetime_normalizer.reading.meridiem import Meridiem
from datetime_normalizer.reading.time import TimeReading
from datetime_normalizer.reading.time_zone_reader import TimeZoneReader


class TimeReader:
    """
    Read the time and time zones that follow a date in canonical text.

    Parameters
    ----------
    time_zone_reader : TimeZoneReader
        Reader of the time zones in the text.
    """

    _MAX_HOUR: ClassVar[int] = 47
    _MICROSECOND_DIGIT_COUNT: ClassVar[int] = 6
    _SEPARATOR: ClassVar[str] = r"(?:t|,?\s*)"
    # The zone may come first: 日本時間午後1時. Lazy, to leave 午後 to the meridiem.
    _LEADING_ZONE: ClassVar[str] = (
        r"(?:\(?(?P<leading_zone>(?!午前|午後|(?:am|pm)(?![a-z]))"
        + rf"(?:[a-z][a-z0-9_+/-]*?|{TimeZoneReader.JAPANESE_NAME}?))\)?\s*)?"
    )
    _LEADING_MERIDIEM: ClassVar[str] = r"(?:(?P<leading_meridiem>午前|午後|am|pm)\s*)?"
    _TRAILING_MERIDIEM: ClassVar[str] = r"(?:\s*(?P<trailing_meridiem>am|pm)(?![a-z]))?"
    # A second zone is a note on the first: +09:00[Asia/Tokyo], GMT+0900 (日本標準時).
    _ZONE: ClassVar[str] = (
        rf"(?:\s*(?P<zone>{TimeZoneReader.PATTERN}))?"
        + rf"(?:\s*[\[(]!?(?P<noted_zone>{TimeZoneReader.PATTERN})[\])])?"
    )
    _PATTERNS: ClassVar[tuple[re.Pattern[str], ...]] = (
        re.compile(
            _SEPARATOR
            + _LEADING_ZONE
            + _LEADING_MERIDIEM
            + r"(?P<hour>\d{1,2}):(?P<minute>\d{2})"
            + r"(?::(?P<second>\d{2})(?:[.,](?P<fraction>\d+))?)?"
            + _TRAILING_MERIDIEM
            + _ZONE
        ),
        re.compile(
            _SEPARATOR
            + _LEADING_ZONE
            + _LEADING_MERIDIEM
            + r"(?P<hour>\d{1,2})時"
            + r"(?:(?P<half>半)|(?P<minute>\d{1,2})分"
            + r"(?:(?P<second>\d{1,2})(?:[.,](?P<fraction>\d+))?秒)?)?"
            + _TRAILING_MERIDIEM
            + _ZONE
        ),
        re.compile(
            _SEPARATOR
            + _LEADING_ZONE
            + r"(?P<hour>\d{1,2})\s*(?P<trailing_meridiem>am|pm)(?![a-z])"
            + _ZONE
        ),
        re.compile(
            _SEPARATOR
            + _LEADING_ZONE
            + r"(?P<hour>\d{2})(?:(?P<minute>\d{2})"
            + r"(?:(?P<second>\d{2})(?:[.,](?P<fraction>\d+))?)?)?"
            + _ZONE
        ),
    )

    def __init__(self, time_zone_reader: TimeZoneReader) -> None:
        self._time_zone_reader: TimeZoneReader = time_zone_reader

    def read(self, text: str) -> TimeReading:
        """
        Read and validate a time.

        Parameters
        ----------
        text : str
            Canonical text that holds only a time and an optional time zone.

        Returns
        -------
        TimeReading
            The time. A fraction beyond microseconds is truncated.

        Raises
        ------
        UnrecognizedDatetimeError
            If the text is not a supported time, including one with two 12-hour markers, or
            a time zone is unknown.
        AmbiguousDatetimeError
            If the time is 12 o'clock on the Japanese 12-hour clock.
        InvalidDatetimeError
            If the time or the time zone offset does not exist.
        """
        match: re.Match[str] | None = next(
            filter(None, (pattern.fullmatch(text) for pattern in self._PATTERNS)), None
        )
        if match is None:
            raise UnrecognizedDatetimeError(f"No supported time in: {text}")

        groups: dict[str, str | None] = match.groupdict()
        minute_text, second_text = groups.get("minute"), groups.get("second")
        fraction: str | None = groups.get("fraction")
        minute: int | None = 30 if groups.get("half") else int(minute_text) if minute_text else None
        second: int | None = int(second_text) if second_text else None
        if (minute or 0) > 59 or (second or 0) > 59:
            raise InvalidDatetimeError(f"Minute or second out of range in: {text}")
        return TimeReading(
            hour=self._read_hour(groups),
            minute=minute,
            second=second,
            microsecond=(
                int(
                    fraction[: self._MICROSECOND_DIGIT_COUNT].ljust(
                        self._MICROSECOND_DIGIT_COUNT, "0"
                    )
                )
                if fraction
                else None
            ),
            time_zones=tuple(
                self._time_zone_reader.read(zone)
                for zone in (groups.get("leading_zone"), groups["zone"], groups["noted_zone"])
                if zone is not None
            ),
        )

    @classmethod
    def _read_hour(cls, groups: dict[str, str | None]) -> int:
        hour_text: str | None = groups["hour"]
        if hour_text is None:
            raise UnrecognizedDatetimeError("No hour in the time")
        hour: int = int(hour_text)
        leading, trailing = groups.get("leading_meridiem"), groups.get("trailing_meridiem")
        if leading is not None and trailing is not None:
            raise UnrecognizedDatetimeError(f"Two 12-hour markers: {leading} and {trailing}")
        meridiem_text: str | None = leading or trailing
        if meridiem_text is not None:
            return Meridiem(meridiem_text).to_24_hour(hour)
        if hour > cls._MAX_HOUR:
            raise InvalidDatetimeError(f"Hour out of range: {hour}")
        return hour
