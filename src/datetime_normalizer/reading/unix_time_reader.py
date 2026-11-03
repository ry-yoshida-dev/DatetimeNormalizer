import re
from datetime import UTC, datetime, timedelta
from typing import ClassVar


class UnixTimeReader:
    """Read seconds or milliseconds since 1970 from canonical text."""

    _EPOCH: ClassVar[datetime] = datetime(1970, 1, 1, tzinfo=UTC)
    # 2001 to 2030. A number from 19 on stays a compact date and hour, such as 1999123113.
    _SECONDS_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"(?P<seconds>1[0-8]\d{8})(?:\.(?P<fraction>\d{1,6}))?"
    )
    _MILLISECONDS_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"\d{13}")

    @classmethod
    def read(cls, text: str) -> datetime | None:
        """
        Read a Unix time.

        Parameters
        ----------
        text : str
            Canonical text.

        Returns
        -------
        datetime | None
            The moment in UTC, or ``None`` when the text is not a Unix time.
        """
        if cls._MILLISECONDS_PATTERN.fullmatch(text):
            return cls._EPOCH + timedelta(milliseconds=int(text))
        match: re.Match[str] | None = cls._SECONDS_PATTERN.fullmatch(text)
        if match is None:
            return None
        return cls._EPOCH + timedelta(
            seconds=int(match["seconds"]),
            microseconds=int((match["fraction"] or "").ljust(6, "0")),
        )
