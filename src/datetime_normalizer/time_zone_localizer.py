from collections.abc import Sequence
from datetime import UTC, datetime, timedelta, tzinfo

from datetime_normalizer.errors import InvalidDatetimeError


class TimeZoneLocalizer:
    """Place a wall clock time in the time zones stated for it, whatever clocks did there."""

    @classmethod
    def localize(cls, wall_clock: datetime, time_zones: Sequence[tzinfo]) -> datetime:
        """
        Attach time zones to a wall clock time.

        A time skipped when clocks move forward moves ahead by the length of the skip. A time
        repeated when clocks move back is the earlier one, unless another time zone tells which.
        Time zones that disagree are read as a conversion: the first one fixes the moment, and
        the last one expresses it, so ``13:05+08:00[Asia/Tokyo]`` is ``14:05+09:00``.

        Parameters
        ----------
        wall_clock : datetime
            A naive time.
        time_zones : Sequence[tzinfo]
            The time zones stated for it. The last one is attached, so ``+09:00[Asia/Tokyo]``
            keeps the region. With none, the time stays naive.

        Returns
        -------
        datetime
            The time, with the ``fold`` that matches the offset.

        Raises
        ------
        InvalidDatetimeError
            If the moment is out of the range of ``datetime`` in the last time zone.
        """
        if not time_zones:
            return wall_clock
        offsets: set[timedelta] = set[timedelta].intersection(
            *(cls._offsets(wall_clock, time_zone) for time_zone in time_zones)
        )
        last_time_zone: tzinfo = time_zones[-1]
        if offsets:
            return next(
                candidate
                for candidate in (
                    wall_clock.replace(tzinfo=last_time_zone, fold=fold) for fold in (0, 1)
                )
                if candidate.utcoffset() in offsets
            )
        try:
            # Through UTC, because converting to the same tzinfo would return the time unchanged.
            return (
                wall_clock.replace(tzinfo=time_zones[0], fold=0)
                .astimezone(UTC)
                .astimezone(last_time_zone)
            )
        except OverflowError as error:
            raise InvalidDatetimeError(f"Moment out of range: {wall_clock}") from error

    @staticmethod
    def _offsets(wall_clock: datetime, time_zone: tzinfo) -> set[timedelta]:
        before: timedelta | None = wall_clock.replace(tzinfo=time_zone, fold=0).utcoffset()
        after: timedelta | None = wall_clock.replace(tzinfo=time_zone, fold=1).utcoffset()
        if before is None or after is None:
            raise InvalidDatetimeError(f"Time zone without an offset: {time_zone}")
        # By PEP 495, fold 0 has the offset before a transition. An offset that grows means
        # clocks moved forward over this time, so it was skipped.
        return set() if before < after else {before, after}
