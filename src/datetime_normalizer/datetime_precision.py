from datetime import datetime
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

    def refined_for(self, value: datetime) -> "DatetimePrecision":
        """
        Grow the precision until it shows every unit of a value that moved between time zones.

        Parameters
        ----------
        value : datetime
            The moved value.

        Returns
        -------
        DatetimePrecision
            This precision, or a finer one, and never coarser than an hour.
        """
        finest: DatetimePrecision = (
            DatetimePrecision.MICROSECOND
            if value.microsecond
            else DatetimePrecision.SECOND
            if value.second
            else DatetimePrecision.MINUTE
            if value.minute
            else DatetimePrecision.HOUR
        )
        return max(self, finest, key=list(DatetimePrecision).index)
