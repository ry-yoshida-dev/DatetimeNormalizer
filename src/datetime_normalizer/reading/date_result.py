from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DateReading:
    """
    Validated date at the start of a text, and the text after it.

    Parameters
    ----------
    year : int
        Gregorian year.
    month : int | None
        Month, or ``None`` when the text states only the year.
    day : int | None
        Day of the month, or ``None`` when the text does not state it.
    rest : str
        The text after the date.
    """

    year: int
    month: int | None
    day: int | None
    rest: str
