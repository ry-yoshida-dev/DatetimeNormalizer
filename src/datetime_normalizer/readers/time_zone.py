import re
from collections.abc import Mapping
from datetime import UTC, timedelta, timezone, tzinfo
from functools import cache
from typing import ClassVar
from zoneinfo import ZoneInfo, available_timezones

from datetime_normalizer.errors import (
    InvalidConfigurationError,
    InvalidDatetimeError,
    UnrecognizedDatetimeError,
)
from datetime_normalizer.text import TextCanonicalizer


class TimeZoneReader:
    """
    Read a time zone from an offset, an abbreviation, an IANA name, or a Japanese name.

    Abbreviations hold their fixed offset, so ``EST`` in July is still -05:00. Names of regions
    follow the daylight saving time of the date, so ``米国東部時間`` is -04:00 in July. An
    abbreviation shared by several time zones means the most common one: ``CST`` is -06:00.

    Parameters
    ----------
    abbreviations : Mapping[str, tzinfo] | None
        Readings of names, which take precedence over the built-in ones, such as ``CST`` for
        China Standard Time.

    Raises
    ------
    InvalidConfigurationError
        If a key of ``abbreviations`` cannot appear in text as a time zone name.
    """

    JAPANESE_NAME: ClassVar[str] = "[ぁ-ヿ㐀-鿿][ぁ-ヿ㐀-鿿-]*"
    # An offset comes first, because utc+9 also looks like a name.
    PATTERN: ClassVar[str] = (
        r"(?:utc|gmt)?\s*[-+]\d{1,2}(?::?\d{2}(?::?\d{2})?)?"
        + rf"|[a-z][a-z0-9_+/-]*|{JAPANESE_NAME}"
    )

    _NAME_PATTERN: ClassVar[re.Pattern[str]] = re.compile(rf"[a-z][a-z0-9_+/-]*|{JAPANESE_NAME}")
    _OFFSET_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"(?:utc|gmt)?\s*(?P<sign>[-+])(?P<hour>\d{1,2})"
        + r"(?::?(?P<minute>\d{2})(?::?(?P<second>\d{2}))?)?"
    )
    # The offsets in use.
    _MIN_OFFSET: ClassVar[timedelta] = timedelta(hours=-12)
    _MAX_OFFSET: ClassVar[timedelta] = timedelta(hours=14)
    _FIXED_ZONES: ClassVar[dict[str, timezone]] = {
        name: UTC if hours == 0 else timezone(timedelta(hours=hours))
        for name, hours in {
            "z": 0,
            "utc": 0,
            "gmt": 0,
            "wet": 0,
            "west": 1,
            "cet": 1,
            "cest": 2,
            "eet": 2,
            "eest": 3,
            "wat": 1,
            "cat": 2,
            "sast": 2,
            "eat": 3,
            "pkt": 5,
            "npt": 5.75,
            "ict": 7,
            "wib": 7,
            "wita": 8,
            "hkt": 8,
            "sgt": 8,
            "pht": 8,
            "awst": 8,
            "jst": 9,
            "kst": 9,
            "wit": 9,
            "acst": 9.5,
            "acdt": 10.5,
            "aest": 10,
            "aedt": 11,
            "nzst": 12,
            "nzdt": 13,
            "ndt": -2.5,
            "nst": -3.5,
            "edt": -4,
            "est": -5,
            "mdt": -6,
            "pdt": -7,
            "akdt": -8,
            "akst": -9,
            "hst": -10,
            # Shared with other zones, as CST with China and Cuba. The most common one is meant.
            "adt": -3,
            "amt": -4,
            "ast": -4,
            "bdt": 6,
            "bst": 1,
            "cdt": -5,
            "cst": -6,
            "ect": -5,
            "gst": 4,
            "ist": 5.5,
            "mst": -7,
            "pst": -8,
            "sst": -11,
            "wst": 13,
            "日本時間": 9,
            "日本標準時": 9,
            "協定世界時": 0,
            "世界協定時": 0,
            "世界標準時": 0,
            "世界時": 0,
            "世界時間": 0,
            "グリニッジ標準時": 0,
            "東部標準時": -5,
            "東部夏時間": -4,
            "中部標準時": -6,
            "中部夏時間": -5,
            "山岳部標準時": -7,
            "山岳部夏時間": -6,
            "太平洋標準時": -8,
            "太平洋夏時間": -7,
        }.items()
    }
    _REGIONS: ClassVar[dict[str, str]] = {
        TextCanonicalizer.canonicalize(name): key
        for name, key in {
            "et": "America/New_York",
            "ct": "America/Chicago",
            "mt": "America/Denver",
            "pt": "America/Los_Angeles",
            # An old IANA name, which some systems leave out of their time zone database.
            "japan": "Asia/Tokyo",
            "米国東部時間": "America/New_York",
            "米国中部時間": "America/Chicago",
            "米国山岳部時間": "America/Denver",
            "米国太平洋時間": "America/Los_Angeles",
            "ニューヨーク時間": "America/New_York",
            "シカゴ時間": "America/Chicago",
            "ロサンゼルス時間": "America/Los_Angeles",
            "ハワイ時間": "Pacific/Honolulu",
            "ロンドン時間": "Europe/London",
            "英国時間": "Europe/London",
            "イギリス時間": "Europe/London",
            "パリ時間": "Europe/Paris",
            "フランス時間": "Europe/Paris",
            "ベルリン時間": "Europe/Berlin",
            "ドイツ時間": "Europe/Berlin",
            "モスクワ時間": "Europe/Moscow",
            "インド時間": "Asia/Kolkata",
            "インド標準時": "Asia/Kolkata",
            "タイ時間": "Asia/Bangkok",
            "ベトナム時間": "Asia/Ho_Chi_Minh",
            "シンガポール時間": "Asia/Singapore",
            "香港時間": "Asia/Hong_Kong",
            "台湾時間": "Asia/Taipei",
            "中国時間": "Asia/Shanghai",
            "中国標準時": "Asia/Shanghai",
            "北京時間": "Asia/Shanghai",
            "韓国時間": "Asia/Seoul",
            "韓国標準時": "Asia/Seoul",
            "シドニー時間": "Australia/Sydney",
        }.items()
    }

    def __init__(self, abbreviations: Mapping[str, tzinfo] | None = None) -> None:
        self._abbreviations: dict[str, tzinfo] = {
            TextCanonicalizer.canonicalize(name): zone
            for name, zone in (abbreviations or {}).items()
        }
        invalid_names: list[str] = [
            name for name in self._abbreviations if not self._NAME_PATTERN.fullmatch(name)
        ]
        if invalid_names:
            raise InvalidConfigurationError(f"Not usable as time zone names: {invalid_names}")

    def resolve(self, time_zone: tzinfo | str) -> tzinfo:
        """
        Turn a time zone given by a caller into a ``tzinfo``.

        Parameters
        ----------
        time_zone : tzinfo | str
            A ``tzinfo``, which is returned as is, or text in any notation of ``read``.

        Returns
        -------
        tzinfo
            The time zone.

        Raises
        ------
        UnrecognizedDatetimeError
            If the name is unknown.
        InvalidDatetimeError
            If the offset does not exist.
        """
        if isinstance(time_zone, tzinfo):
            return time_zone
        return self.read(TextCanonicalizer.canonicalize(time_zone))

    def read(self, text: str) -> tzinfo:
        """
        Read a time zone.

        Parameters
        ----------
        text : str
            Canonical text that holds only a time zone.

        Returns
        -------
        tzinfo
            A fixed offset, or a ``ZoneInfo`` for the name of a region.

        Raises
        ------
        UnrecognizedDatetimeError
            If the name is unknown. Without a time zone database, that is every IANA name.
        InvalidDatetimeError
            If the offset does not exist.
        """
        offset_match: re.Match[str] | None = self._OFFSET_PATTERN.fullmatch(text)
        if offset_match is not None:
            return self._read_offset(offset_match)
        custom_zone: tzinfo | None = self._abbreviations.get(text)
        if custom_zone is not None:
            return custom_zone
        fixed_zone: timezone | None = self._FIXED_ZONES.get(text)
        if fixed_zone is not None:
            return fixed_zone
        key: str | None = self._iana_keys().get(self._REGIONS.get(text, text).lower())
        if key is None:
            raise UnrecognizedDatetimeError(f"Unknown time zone: {text}")
        return ZoneInfo(key)

    @classmethod
    def _read_offset(cls, match: re.Match[str]) -> timezone:
        minutes, seconds = int(match["minute"] or 0), int(match["second"] or 0)
        magnitude: timedelta = timedelta(hours=int(match["hour"]), minutes=minutes, seconds=seconds)
        offset: timedelta = -magnitude if match["sign"] == "-" else magnitude
        if minutes > 59 or seconds > 59 or not cls._MIN_OFFSET <= offset <= cls._MAX_OFFSET:
            raise InvalidDatetimeError(f"Time zone offset out of range: {match.group()}")
        return timezone(offset)

    @staticmethod
    @cache
    def _iana_keys() -> dict[str, str]:
        # Canonical text is lower case, while the keys of the database are not.
        return {key.lower(): key for key in available_timezones() - {"Factory"}}
