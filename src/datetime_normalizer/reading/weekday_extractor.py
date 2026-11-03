import re
from calendar import Day
from typing import ClassVar

from datetime_normalizer.reading.weekday_extraction import WeekdayExtraction


class WeekdayExtractor:
    """Take the weekday out of canonical text, in Japanese or in English."""

    _KANJI: ClassVar[str] = "[月火水木金土日]"
    _ENGLISH: ClassVar[str] = (
        "monday|mon|tuesday|tues|tue|wednesday|wed|thursday|thurs|thur|thu"
        + "|friday|fri|saturday|sat|sunday|sun"
    )
    _PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        rf"\(({_KANJI})(?:曜日?)?\)|({_KANJI})曜日?|\(({_ENGLISH})\)|(?<![a-z])({_ENGLISH})(?![a-z]),?"
    )
    _WEEKDAYS: ClassVar[dict[str, Day]] = {
        "月": Day.MONDAY,
        "火": Day.TUESDAY,
        "水": Day.WEDNESDAY,
        "木": Day.THURSDAY,
        "金": Day.FRIDAY,
        "土": Day.SATURDAY,
        "日": Day.SUNDAY,
        "mon": Day.MONDAY,
        "tue": Day.TUESDAY,
        "wed": Day.WEDNESDAY,
        "thu": Day.THURSDAY,
        "fri": Day.FRIDAY,
        "sat": Day.SATURDAY,
        "sun": Day.SUNDAY,
    }

    @classmethod
    def extract(cls, text: str) -> WeekdayExtraction:
        """
        Split the first weekday from a text.

        Parameters
        ----------
        text : str
            Canonical text.

        Returns
        -------
        WeekdayExtraction
            The rest of the text and the weekday.
        """
        match: re.Match[str] | None = cls._PATTERN.search(text)
        if match is None:
            return WeekdayExtraction(text=text, weekday=None)
        token: str = "".join(group for group in match.groups() if group)
        rest: str = f"{text[: match.start()]} {text[match.end() :]}".strip()
        return WeekdayExtraction(text=rest, weekday=cls._WEEKDAYS[token[:3]])
