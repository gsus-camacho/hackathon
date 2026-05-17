class RecommendationsError(Exception):
    """Base error for recommendations module."""


class AIBackendError(RecommendationsError):
    pass
