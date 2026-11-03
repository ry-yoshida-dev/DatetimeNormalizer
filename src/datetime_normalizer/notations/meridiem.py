from enum import Enum

from datetime_normalizer.errors import AmbiguousDatetimeError, InvalidDatetimeError


class Meridiem(Enum):
    """Marker of the half of the day, in the notation it was written."""

    AM = "am"
    PM = "pm"
    GOZEN = "午前"
    GOGO = "午後"

    def to_24_hour(self, hour: int) -> int:
        """
        Convert an hour of the 12-hour clock.

        Parameters
        ----------
        hour : int
            Hour as written after this marker.

        Returns
        -------
        int
            Hour of the 24-hour clock.

        Raises
        ------
        AmbiguousDatetimeError
            If the hour is 12 on the Japanese clock, where 午後12時 is both midnight by the
            original definition and noon in common use.
        InvalidDatetimeError
            If the hour does not exist on the clock of this marker.
        """
        match self:
            case Meridiem.AM | Meridiem.PM if not 1 <= hour <= 12:
                raise InvalidDatetimeError(f"Hour must be 1 to 12 with {self.value}, got {hour}")
            case Meridiem.AM:
                return hour % 12
            case Meridiem.PM:
                return hour % 12 + 12
            case Meridiem.GOZEN | Meridiem.GOGO if hour > 12:
                raise InvalidDatetimeError(f"Hour must be 0 to 11 with {self.value}, got {hour}")
            case Meridiem.GOZEN | Meridiem.GOGO if hour == 12:
                raise AmbiguousDatetimeError(
                    f"{self.value}12時 can mean noon or midnight; write it on the 24-hour clock"
                )
            case Meridiem.GOZEN:
                return hour
            case Meridiem.GOGO:
                return hour + 12
