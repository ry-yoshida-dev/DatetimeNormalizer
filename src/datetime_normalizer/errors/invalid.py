from datetime_normalizer.errors.base import DatetimeNormalizationError


class InvalidDatetimeError(DatetimeNormalizationError):
    """The notation is supported, but the date or time it names cannot exist."""
