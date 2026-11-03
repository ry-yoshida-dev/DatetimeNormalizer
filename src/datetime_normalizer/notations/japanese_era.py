from datetime import date
from enum import Enum


class JapaneseEra(Enum):
    """
    Japanese eras whose dates are on the Gregorian calendar.

    An era's first and last day can coincide with those of its neighbor, because an era that
    ended by the death of an emperor changed during the day. Meiji starts when Japan adopted
    the Gregorian calendar: dates of Meiji 1 to 5 are lunisolar and cannot be converted by
    arithmetic.
    """

    MEIJI = ("明治", "明", "m", 1868, date(1873, 1, 1), date(1912, 7, 30))
    TAISHO = ("大正", "大", "t", 1912, date(1912, 7, 30), date(1926, 12, 25))
    SHOWA = ("昭和", "昭", "s", 1926, date(1926, 12, 25), date(1989, 1, 7))
    HEISEI = ("平成", "平", "h", 1989, date(1989, 1, 8), date(2019, 4, 30))
    REIWA = ("令和", "令", "r", 2019, date(2019, 5, 1), date.max)

    def __init__(
        self,
        label: str,
        short_label: str,
        letter: str,
        first_year: int,
        first_day: date,
        last_day: date,
    ) -> None:
        self.label: str = label
        self.short_label: str = short_label
        self.letter: str = letter
        self.first_year: int = first_year
        self.first_day: date = first_day
        self.last_day: date = last_day

    def to_gregorian_year(self, era_year: int) -> int:
        """
        Convert a year of this era.

        Parameters
        ----------
        era_year : int
            Year counted from this era, where the first year is 1.

        Returns
        -------
        int
            The Gregorian year.
        """
        return self.first_year + era_year - 1

    def overlaps(self, first_day: date, last_day: date) -> bool:
        """
        Tell whether a span of days has any day in this era.

        Parameters
        ----------
        first_day : date
            First day of the span.
        last_day : date
            Last day of the span.

        Returns
        -------
        bool
            True when at least one day of the span lies in this era.
        """
        return self.first_day <= last_day and first_day <= self.last_day
