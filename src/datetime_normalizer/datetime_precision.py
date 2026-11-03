from enum import Enum


class DatetimePrecision(Enum):
    """Smallest unit stated in the normalized text."""

    YEAR = "year"
    MONTH = "month"
    DAY = "day"
    HOUR = "hour"
    MINUTE = "minute"
    SECOND = "second"
    MICROSECOND = "microsecond"
