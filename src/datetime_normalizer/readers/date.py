import re
from calendar import monthrange
from datetime import date
from typing import ClassVar

from datetime_normalizer.errors import (
    AmbiguousDatetimeError,
    InvalidDatetimeError,
    UnrecognizedDatetimeError,
)
from datetime_normalizer.notations import DateOrder, JapaneseEra
from datetime_normalizer.results import DateResult


class DateReader:
    """
    Read the date at the start of canonical text.

    Parameters
    ----------
    date_order : DateOrder | None
        Order of the month and day in dates written with the year last, or ``None`` to
        reject those dates as ambiguous.
    """

    _ERAS: ClassVar[dict[str, JapaneseEra]] = {
        name: era for era in JapaneseEra for name in (era.label, era.short_label, era.letter)
    }
    _ERA: ClassVar[str] = "|".join(sorted(_ERAS, key=len, reverse=True))
    _MONTH_NAMES: ClassVar[dict[str, int]] = {
        name: number
        for number, name in enumerate(
            ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"),
            start=1,
        )
    }
    _MONTH_NAME: ClassVar[str] = (
        "january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug"
        + "|september|sept|sep|october|oct|november|nov|december|dec"
    )
    _ORDINAL: ClassVar[str] = "(?:st|nd|rd|th)?"

    # Tried in order. Every pattern names the groups it fills, so reading needs no dispatch.
    _PATTERNS: ClassVar[tuple[re.Pattern[str], ...]] = (
        re.compile(
            rf"(?:(?P<era>{_ERA})[.\s]*)?(?P<year>\d{{1,4}})年"
            + r"(?:(?P<month>\d{1,2})月(?:(?P<day>\d{1,2})日)?)?"
        ),
        re.compile(
            rf"(?P<era>{_ERA})[.\s]*(?P<year>\d{{1,3}})(?P<separator>[-/.])(?P<month>\d{{1,2}})"
            + r"(?:(?P=separator)(?P<day>\d{1,2}))?(?!\d)"
        ),
        re.compile(
            r"(?P<year>\d{4})(?P<separator>[-/.:])(?P<month>\d{1,2})"
            + r"(?:(?P=separator)(?P<day>\d{1,2}))?(?!\d)"
        ),
        re.compile(r"(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})"),
        re.compile(
            r"(?P<first>\d{1,2})(?P<separator>[-/.])(?P<second>\d{1,2})(?P=separator)"
            + r"(?P<year>\d{4})(?!\d)"
        ),
        re.compile(
            rf"(?P<month_name>{_MONTH_NAME})\.?\s*(?P<day>\d{{1,2}}){_ORDINAL},?\s+"
            + r"(?P<year>\d{4})(?!\d)"
        ),
        re.compile(
            rf"(?P<day>\d{{1,2}}){_ORDINAL}[-\s](?P<month_name>{_MONTH_NAME})\.?,?[-\s]"
            + r"(?P<year>\d{4})(?!\d)"
        ),
        re.compile(rf"(?P<month_name>{_MONTH_NAME})\.?,?\s+(?P<year>\d{{4}})(?!\d)"),
        re.compile(r"(?P<year>\d{4})(?!\d)"),
        re.compile(r"(?P<month>\d{1,2})月(?:(?P<day>\d{1,2})日)?"),
        # Only slashes: 1-5 and 1.5 are more often a range and a decimal than a date.
        re.compile(r"(?P<first>\d{1,2})/(?P<second>\d{1,2})(?![\d/])"),
        re.compile(rf"(?P<month_name>{_MONTH_NAME})\.?\s*(?P<day>\d{{1,2}}){_ORDINAL}(?![\da-z])"),
        re.compile(rf"(?P<day>\d{{1,2}}){_ORDINAL}[-\s](?P<month_name>{_MONTH_NAME})\.?(?![a-z])"),
    )
    _SHORT_YEAR_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"\d{1,2}(?P<separator>[-/.])\d{1,2}(?P=separator)\d{1,2}(?!\d)"
    )
    # After a date without a year, a number that is not clearly an hour may be a short year:
    # 5 Jan 24, and 5 Jan 24 JST.
    _LONE_NUMBER_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"\s*,?\s*\d+(?!\d|:|時|\s*(?:am|pm))"
    )

    def __init__(self, date_order: DateOrder | None = None) -> None:
        self._date_order: DateOrder | None = date_order

    def read(self, text: str, default_year: int | None = None) -> DateResult:
        """
        Read and validate a date.

        Parameters
        ----------
        text : str
            Canonical text starting with a date.
        default_year : int | None
            Year of a date that does not state one, or ``None`` to reject those dates as
            ambiguous. A year in the text takes precedence.

        Returns
        -------
        DateResult
            The date and the text after it.

        Raises
        ------
        UnrecognizedDatetimeError
            If the text does not start with a supported date.
        AmbiguousDatetimeError
            If the year, its century, or the order of month and day, is not stated.
        InvalidDatetimeError
            If the date does not exist.
        """
        if self._SHORT_YEAR_PATTERN.match(text):
            raise AmbiguousDatetimeError(f"Cannot tell the year and its century in: {text}")
        match: re.Match[str] | None = next(
            filter(None, (pattern.match(text) for pattern in self._PATTERNS)), None
        )
        if match is None:
            raise UnrecognizedDatetimeError(f"No supported date in: {text}")

        groups: dict[str, str | None] = match.groupdict()
        month, day = self._read_month_and_day(groups, text)
        rest: str = text[match.end() :]
        if groups.get("year") is None and self._LONE_NUMBER_PATTERN.match(rest):
            raise AmbiguousDatetimeError(f"Cannot tell a short year from an hour in: {text}")
        year: int = self._read_year(groups, default_year, text)
        self._validate(year, month, day)
        self._validate_era(groups.get("era"), year, month, day)
        return DateResult(year=year, month=month, day=day, rest=rest)

    def _read_month_and_day(
        self, groups: dict[str, str | None], text: str
    ) -> tuple[int | None, int | None]:
        first, second = groups.get("first"), groups.get("second")
        if first is not None and second is not None:
            match self._date_order:
                case None:
                    raise AmbiguousDatetimeError(
                        f"Cannot tell the month from the day; set date_order to read: {text}"
                    )
                case DateOrder.MONTH_FIRST:
                    return int(first), int(second)
                case DateOrder.DAY_FIRST:
                    return int(second), int(first)
        month_name, month, day = groups.get("month_name"), groups.get("month"), groups.get("day")
        month_number: int | None = (
            self._MONTH_NAMES[month_name[:3]] if month_name else int(month) if month else None
        )
        return month_number, int(day) if day else None

    def _read_year(self, groups: dict[str, str | None], default_year: int | None, text: str) -> int:
        year_text: str | None = groups.get("year")
        if year_text is None:
            if default_year is None:
                raise AmbiguousDatetimeError(f"No year; set default_year to read: {text}")
            return default_year
        era_name: str | None = groups.get("era")
        if era_name is not None:
            return self._ERAS[era_name].to_gregorian_year(int(year_text))
        if len(year_text) != 4:
            raise AmbiguousDatetimeError(f"Cannot tell the era or century of the year in: {text}")
        return int(year_text)

    @staticmethod
    def _validate(year: int, month: int | None, day: int | None) -> None:
        if not date.min.year <= year <= date.max.year:
            raise InvalidDatetimeError(f"Year out of range: {year}")
        if month is not None and not 1 <= month <= 12:
            raise InvalidDatetimeError(f"Month out of range: {month}")
        if month is not None and day is not None and not 1 <= day <= monthrange(year, month)[1]:
            raise InvalidDatetimeError(f"Day out of range: {year}-{month}-{day}")

    def _validate_era(
        self, era_name: str | None, year: int, month: int | None, day: int | None
    ) -> None:
        if era_name is None:
            return
        era: JapaneseEra = self._ERAS[era_name]
        last_month: int = month or 12
        first_day: date = date(year, month or 1, day or 1)
        last_day: date = date(year, last_month, day or monthrange(year, last_month)[1])
        if not era.overlaps(first_day, last_day):
            raise InvalidDatetimeError(
                f"{first_day} to {last_day} is not in {era.label} "
                + f"({era.first_day} to {era.last_day})"
            )
