import re
from datetime import tzinfo
from typing import ClassVar

from datetime_normalizer.errors import (
    AmbiguousDatetimeError,
    InvalidDatetimeError,
    UnrecognizedDatetimeError,
)
from datetime_normalizer.notations import Meridiem
from datetime_normalizer.readers.time_zone import TimeZoneReader
from datetime_normalizer.results import TimeResult


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
    _MAX_OFFSET_DIGITS_WITHOUT_SECONDS: ClassVar[int] = 4
    _SEPARATOR: ClassVar[str] = r"(?:(?P<iso_separator>t)|\s*,?\s*)"
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
    # A t before a digit starts a time, as in 2024-01-05t13, rather than a time zone name.
    _TIME_ZONES_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"\s*,?\s*(?!t\d)" + _ZONE)

    def __init__(self, time_zone_reader: TimeZoneReader) -> None:
        self._time_zone_reader: TimeZoneReader = time_zone_reader

    def read(self, text: str) -> TimeResult:
        """
        Read and validate a time.

        Parameters
        ----------
        text : str
            Canonical text that holds only a time and an optional time zone.

        Returns
        -------
        TimeResult
            The time. A fraction beyond microseconds is truncated.

        Raises
        ------
        UnrecognizedDatetimeError
            If the text is not a supported time, including one with two 12-hour markers, or
            a time zone is unknown.
        AmbiguousDatetimeError
            If the time is 12 o'clock on the Japanese 12-hour clock, or a negative offset may be
            the end of a range.
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
        return TimeResult(
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
            time_zones=self._read_time_zones(groups, text),
        )

    def read_time_zones(self, text: str) -> tuple[tzinfo, ...]:
        """
        Read time zones that follow a date directly, without a time.

        Parameters
        ----------
        text : str
            Canonical text after a date.

        Returns
        -------
        tuple[tzinfo, ...]
            The time zones, which are empty when the text is anything else, such as a time.

        Raises
        ------
        UnrecognizedDatetimeError
            If a time zone name is unknown.
        AmbiguousDatetimeError
            If a negative offset may be the end of a range.
        InvalidDatetimeError
            If the time zone offset does not exist.
        """
        match: re.Match[str] | None = self._TIME_ZONES_PATTERN.fullmatch(text)
        return () if match is None else self._read_time_zones(match.groupdict(), text)

    def _read_time_zones(self, groups: dict[str, str | None], text: str) -> tuple[tzinfo, ...]:
        if self._is_range_like(groups):
            raise AmbiguousDatetimeError(
                f"A negative offset or the end of a range; write T, seconds, or UTC-05:00: {text}"
            )
        return tuple(
            self._time_zone_reader.read(zone)
            for zone in (groups.get("leading_zone"), groups["zone"], groups["noted_zone"])
            if zone is not None
        )

    @classmethod
    def _is_range_like(cls, groups: dict[str, str | None]) -> bool:
        # 10:00-11:00 is more often a range. ISO 8601 output, a note on the offset, and seconds
        # on the time alone, as in str(datetime), all show that it is an offset.
        zone: str | None = groups["zone"]
        if (
            zone is None
            or not zone.startswith("-")
            or groups.get("iso_separator")
            or groups["noted_zone"]
        ):
            return False
        return (
            groups.get("second") is None
            or sum(map(str.isdigit, zone)) > cls._MAX_OFFSET_DIGITS_WITHOUT_SECONDS
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
