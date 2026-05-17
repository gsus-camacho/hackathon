"""Planifications module errors."""


class PlanificationsError(Exception):
    """Base error for planifications module."""


class InsufficientHistoryError(PlanificationsError):
    """Not enough purchase history to generate plan."""


class AllergenConflictError(PlanificationsError):
    """Product conflicts with student's dietary/allergen profile."""