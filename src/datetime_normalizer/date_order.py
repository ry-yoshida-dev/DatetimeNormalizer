from enum import Enum


class DateOrder(Enum):
    """Order of the month and day in dates written with the year last, such as ``1/2/2024``."""

    MONTH_FIRST = "month_first"
    DAY_FIRST = "day_first"
