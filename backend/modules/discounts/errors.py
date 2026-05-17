class DiscountsError(Exception):
    """Base error for discounts module."""


class InvalidPackageError(DiscountsError):
    pass


class PackageNotFoundError(DiscountsError):
    pass
