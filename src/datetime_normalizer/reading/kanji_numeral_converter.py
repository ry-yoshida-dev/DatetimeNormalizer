import re
from typing import ClassVar


class KanjiNumeralConverter:
    """Replace positional (二〇二四) and unit-based (二千二十四) kanji numerals with digits."""

    _DIGITS: ClassVar[dict[str, str]] = dict(
        zip("〇零一二三四五六七八九", "00123456789", strict=True)
    )
    _POSITIONAL_TABLE: ClassVar[dict[int, str]] = str.maketrans(_DIGITS)
    _NUMERAL_PATTERN: ClassVar[re.Pattern[str]] = re.compile("[〇零一二三四五六七八九十百千]+")
    _UNIT_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        "(?:([一二三四五六七八九]?)千)?"
        + "(?:([一二三四五六七八九]?)百)?"
        + "(?:([一二三四五六七八九]?)十)?"
        + "([一二三四五六七八九]?)"
    )

    @classmethod
    def convert(cls, text: str) -> str:
        """
        Replace every kanji numeral in a text.

        Parameters
        ----------
        text : str
            Any text.

        Returns
        -------
        str
            The text with numerals as digits. A malformed numeral such as 十十 is kept, so
            that it fails later instead of being read as a wrong number.
        """
        return cls._NUMERAL_PATTERN.sub(lambda match: cls._to_digits(match.group()), text)

    @classmethod
    def _to_digits(cls, numeral: str) -> str:
        if not set(numeral) & set("十百千"):
            return numeral.translate(cls._POSITIONAL_TABLE)
        match: re.Match[str] | None = cls._UNIT_PATTERN.fullmatch(numeral)
        if match is None:
            return numeral
        thousands, hundreds, tens, ones = match.groups()
        return str(
            cls._coefficient(thousands) * 1000
            + cls._coefficient(hundreds) * 100
            + cls._coefficient(tens) * 10
            + (int(cls._DIGITS[ones]) if ones else 0)
        )

    @classmethod
    def _coefficient(cls, digit: str | None) -> int:
        # None means the unit is absent, and an empty digit means a bare unit such as 十.
        if digit is None:
            return 0
        return int(cls._DIGITS[digit]) if digit else 1
