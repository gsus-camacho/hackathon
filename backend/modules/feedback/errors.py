class FeedbackError(Exception):
    """Base error for feedback module."""


class InvalidRatingError(FeedbackError):
    pass
