from calendar import Day
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WeekdayExtraction:
    """
    Text split into its stated weekday and everything else.

    Parameters
    ----------
    text : str
        The text without the weekday.
    weekday : Day | None
        The stated weekday, or ``None`` when the text states none.
    """

    text: str
    weekday: Day | None
