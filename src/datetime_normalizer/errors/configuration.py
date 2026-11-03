from datetime_normalizer.errors.base import DatetimeNormalizationError


class InvalidConfigurationError(DatetimeNormalizationError):
    """An argument that configures the normalizer cannot be used."""
