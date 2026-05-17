class PlanificationsError(Exception):
    """Base error for planifications module."""


class InsufficientHistoryError(PlanificationsError):
    pass
