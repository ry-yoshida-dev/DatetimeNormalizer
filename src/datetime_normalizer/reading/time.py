from dataclasses import dataclass
from datetime import tzinfo


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
    time_zones : tuple[tzinfo, ...]
        Stated time zones, which are empty when the text states none. There are several when
        one is a note on another, as in ``+09:00[Asia/Tokyo]``.
    """

    hour: int
    minute: int | None
    second: int | None
    microsecond: int | None
    time_zones: tuple[tzinfo, ...]
