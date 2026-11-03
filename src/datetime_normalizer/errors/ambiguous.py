from datetime_normalizer.errors.base import DatetimeNormalizationError


class AmbiguousDatetimeError(DatetimeNormalizationError):
    """The text has several plausible readings, and guessing could silently corrupt it."""
