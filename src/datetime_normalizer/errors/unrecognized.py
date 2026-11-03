from datetime_normalizer.errors.base import DatetimeNormalizationError


class UnrecognizedDatetimeError(DatetimeNormalizationError):
    """The text does not follow any supported notation."""
