from dataclasses import dataclass
from datetime import UTC, datetime, tzinfo

from datetime_normalizer.datetime_precision import DatetimePrecision
from datetime_normalizer.errors import InvalidDatetimeError
from datetime_normalizer.reading import TimeZoneReader


@dataclass(frozen=True, slots=True)
class NormalizedDatetime:
    """
    Date and time read from text, with the precision it was written in.

    Parameters
    ----------
    value : datetime
        The moment. Units below ``precision`` hold their smallest value, so ``2024年1月`` is
        January 1 at midnight. It is naive unless the text or the caller states a time zone.
    precision : DatetimePrecision
        Smallest unit stated in the text.
    """

    value: datetime
    precision: DatetimePrecision

    @property
    def is_timezone_aware(self) -> bool:
        """Whether the text or the caller stated a time zone."""
        return self.value.utcoffset() is not None

    def to_time_zone(self, time_zone: tzinfo | str) -> "NormalizedDatetime":
        """
        Express the same moment in another time zone.

        Parameters
        ----------
        time_zone : tzinfo | str
            The target: a ``tzinfo``, or text such as ``America/New_York``, ``JST``, ``+05:30``,
            or ``ロンドン時間``.

        Returns
        -------
        NormalizedDatetime
            The moment in the target. A naive value is taken to be in UTC. The precision grows
            when the units below it stop being zero, so ``13時`` in JST is ``09:30`` in India,
            not ``09``, and a date without a time gets an hour.

        Raises
        ------
        UnrecognizedDatetimeError
            If the name of the target is unknown.
        InvalidDatetimeError
            If the offset of the target does not exist, or the moment is out of the range of
            ``datetime`` there.
        """
        target: tzinfo = TimeZoneReader().resolve(time_zone)
        aware: datetime = self.value if self.is_timezone_aware else self.value.replace(tzinfo=UTC)
        try:
            converted: datetime = aware.astimezone(target)
        except OverflowError as error:
            raise InvalidDatetimeError(
                f"Moment out of range in {target}: {self.isoformat()}"
            ) from error
        return NormalizedDatetime(value=converted, precision=self.precision.refined_for(converted))

    def to_utc(self) -> "NormalizedDatetime":
        """
        Express the same moment in UTC.

        Returns
        -------
        NormalizedDatetime
            The moment in UTC. A naive value is taken to be in UTC already.

        Raises
        ------
        InvalidDatetimeError
            If the moment is out of the range of ``datetime`` in UTC.
        """
        return self.to_time_zone(UTC)

    def isoformat(self) -> str:
        """
        Format as ISO 8601, without any unit below the precision.

        Returns
        -------
        str
            The canonical text, e.g. ``2024-01``, ``2024-01-05``, or
            ``2024-01-05T13:05:00+09:00``.
        """
        match self.precision:
            case DatetimePrecision.YEAR:
                return f"{self.value.year:04d}"
            case DatetimePrecision.MONTH:
                return f"{self.value.year:04d}-{self.value.month:02d}"
            case DatetimePrecision.DAY:
                return self.value.date().isoformat()
            case DatetimePrecision.HOUR:
                return self.value.isoformat(timespec="hours")
            case DatetimePrecision.MINUTE:
                return self.value.isoformat(timespec="minutes")
            case DatetimePrecision.SECOND:
                return self.value.isoformat(timespec="seconds")
            case DatetimePrecision.MICROSECOND:
                return self.value.isoformat(timespec="microseconds")
