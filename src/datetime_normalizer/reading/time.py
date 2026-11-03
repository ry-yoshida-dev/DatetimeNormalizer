from dataclasses import dataclass
from datetime import timezone


@dataclass(frozen=True, slots=True)
class TimeReading:
    """
    Validated time of day.

    Parameters
    ----------
    hour : int
        Hour from 0 to 47. An hour of 24 or more belongs to the next day, as in 25時.
    minute : int | None
        Minute, or ``None`` when the text does not state it.
    second : int | None
        Second, or ``None`` when the text does not state it.
    microsecond : int | None
        Microsecond, or ``None`` when the text does not state a fraction of a second.
    time_zone : timezone | None
        Stated time zone, or ``None`` when the text states none.
    """

    hour: int
    minute: int | None
    second: int | None
    microsecond: int | None
    time_zone: timezone | None
