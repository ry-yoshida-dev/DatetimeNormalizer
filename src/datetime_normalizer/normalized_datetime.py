from dataclasses import dataclass
from datetime import datetime

from datetime_normalizer.datetime_precision import DatetimePrecision


@dataclass(frozen=True, slots=True)
class NormalizedDatetime:
    """
    Date and time read from text, with the precision it was written in.

    Parameters
    ----------
    value : datetime
        The moment. Units below ``precision`` hold their smallest value, so ``2024年1月`` is
        January 1 at midnight. It is naive unless the text states a time zone.
    precision : DatetimePrecision
        Smallest unit stated in the text.
    """

    value: datetime
    precision: DatetimePrecision

    @property
    def is_timezone_aware(self) -> bool:
        """Whether the text stated a time zone."""
        return self.value.utcoffset() is not None

    def isoformat(self) -> str:
        """
        Format as ISO 8601, without any unit below the precision.

        Returns
        -------
        str
            The canonical text, e.g. ``2024-01``, ``2024-01-05``, or
            ``2024-01-05T13:05:00+09:00``.
        """
        match self.precision:
            case DatetimePrecision.YEAR:
                return f"{self.value.year:04d}"
            case DatetimePrecision.MONTH:
                return f"{self.value.year:04d}-{self.value.month:02d}"
            case DatetimePrecision.DAY:
                return self.value.date().isoformat()
            case DatetimePrecision.HOUR:
                return self.value.isoformat(timespec="hours")
            case DatetimePrecision.MINUTE:
                return self.value.isoformat(timespec="minutes")
            case DatetimePrecision.SECOND:
                return self.value.isoformat(timespec="seconds")
            case DatetimePrecision.MICROSECOND:
                return self.value.isoformat(timespec="microseconds")
