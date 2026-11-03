import re
from datetime import UTC, timedelta, timezone
from typing import ClassVar

from datetime_normalizer.errors import InvalidDatetimeError, UnrecognizedDatetimeError
from datetime_normalizer.reading.meridiem import Meridiem
from datetime_normalizer.reading.time import TimeReading


class TimeReader:
    """Read the time and time zone that follow a date in canonical text."""

    _MAX_HOUR: ClassVar[int] = 47
    _MICROSECOND_DIGIT_COUNT: ClassVar[int] = 6
    _JST: ClassVar[timezone] = timezone(timedelta(hours=9))
    # The offsets in use. Anything beyond is more likely the end of a range: 13:00-15:00.
    _MIN_OFFSET: ClassVar[timedelta] = timedelta(hours=-12)
    _MAX_OFFSET: ClassVar[timedelta] = timedelta(hours=14)
    _NAMED_ZONES: ClassVar[dict[str, timezone]] = {
        "z": UTC,
        "utc": UTC,
        "gmt": UTC,
        "jst": _JST,
        "日本時間": _JST,
    }

    _SEPARATOR: ClassVar[str] = r"(?:t|,?\s*)"
    _LEADING_MERIDIEM: ClassVar[str] = r"(?:(?P<leading_meridiem>午前|午後|am|pm)\s*)?"
    _TRAILING_MERIDIEM: ClassVar[str] = r"(?:\s*(?P<trailing_meridiem>am|pm))?"
    _ZONE: ClassVar[str] = (
        r"(?:\s*(?:(?P<zone_name>z|utc|gmt|jst|日本時間)"
        + r"|(?:utc|gmt)?\s*(?P<sign>[-+])(?P<zone_hour>\d{1,2})(?::?(?P<zone_minute>\d{2}))?))?"
    )
    _PATTERNS: ClassVar[tuple[re.Pattern[str], ...]] = (
        re.compile(
            _SEPARATOR
            + _LEADING_MERIDIEM
            + r"(?P<hour>\d{1,2}):(?P<minute>\d{2})"
            + r"(?::(?P<second>\d{2})(?:[.,](?P<fraction>\d+))?)?"
            + _TRAILING_MERIDIEM
            + _ZONE
        ),
        re.compile(
            _SEPARATOR
            + _LEADING_MERIDIEM
            + r"(?P<hour>\d{1,2})時"
            + r"(?:(?P<half>半)|(?P<minute>\d{1,2})分"
            + r"(?:(?P<second>\d{1,2})(?:[.,](?P<fraction>\d+))?秒)?)?"
            + _TRAILING_MERIDIEM
            + _ZONE
        ),
        re.compile(_SEPARATOR + r"(?P<hour>\d{1,2})\s*(?P<trailing_meridiem>am|pm)" + _ZONE),
        re.compile(
            _SEPARATOR
            + r"(?P<hour>\d{2})(?:(?P<minute>\d{2})"
            + r"(?:(?P<second>\d{2})(?:[.,](?P<fraction>\d+))?)?)?"
            + _ZONE
        ),
    )

    @classmethod
    def read(cls, text: str) -> TimeReading:
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
            If the text is not a supported time, including one with two 12-hour markers.
        AmbiguousDatetimeError
            If the time is 12 o'clock on the Japanese 12-hour clock.
        InvalidDatetimeError
            If the time or the time zone offset does not exist.
        """
        match: re.Match[str] | None = next(
            filter(None, (pattern.fullmatch(text) for pattern in cls._PATTERNS)), None
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
            hour=cls._read_hour(groups),
            minute=minute,
            second=second,
            microsecond=(
                int(
                    fraction[: cls._MICROSECOND_DIGIT_COUNT].ljust(
                        cls._MICROSECOND_DIGIT_COUNT, "0"
                    )
                )
                if fraction
                else None
            ),
            time_zone=cls._read_zone(groups),
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

    @classmethod
    def _read_zone(cls, groups: dict[str, str | None]) -> timezone | None:
        zone_name, sign, zone_hour = groups["zone_name"], groups["sign"], groups["zone_hour"]
        if zone_name is not None:
            return cls._NAMED_ZONES[zone_name]
        if sign is None or zone_hour is None:
            return None
        hours, minutes = int(zone_hour), int(groups["zone_minute"] or 0)
        magnitude: timedelta = timedelta(hours=hours, minutes=minutes)
        offset: timedelta = -magnitude if sign == "-" else magnitude
        if minutes > 59 or not cls._MIN_OFFSET <= offset <= cls._MAX_OFFSET:
            raise InvalidDatetimeError(f"Time zone offset out of range: {sign}{hours}:{minutes}")
        return timezone(offset)
