import re
import unicodedata
from typing import ClassVar

from datetime_normalizer.reading.kanji_numeral_converter import KanjiNumeralConverter


class TextCanonicalizer:
    """Remove character-level differences so that readers only deal with one spelling."""

    _DASH_TABLE: ClassVar[dict[int, str]] = str.maketrans(dict.fromkeys("‐‑‒–—―−ー", "-"))
    _SPACE_AROUND_UNIT_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"\s*([年月日時分秒半])\s*")
    _SPACE_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"\s+")

    @classmethod
    def canonicalize(cls, text: str) -> str:
        """
        Canonicalize characters of a text.

        NFKC folds full-width characters and era ligatures such as ㋿. Letters become lower
        case, dashes become ``-``, and kanji numerals and 元 become digits.

        Parameters
        ----------
        text : str
            Text as given.

        Returns
        -------
        str
            The canonical text.
        """
        folded: str = unicodedata.normalize("NFKC", text).lower().translate(cls._DASH_TABLE)
        spelled: str = (
            KanjiNumeralConverter.convert(folded)
            .replace("元", "1")
            .replace("正午", "12:00")
            .replace("a.m.", "am")
            .replace("p.m.", "pm")
        )
        tight: str = cls._SPACE_AROUND_UNIT_PATTERN.sub(r"\1", spelled)
        return cls._SPACE_PATTERN.sub(" ", tight).strip()
