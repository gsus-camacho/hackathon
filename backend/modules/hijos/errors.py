class HijosError(Exception):
    """Base error for hijos module."""


class HijoNotFoundError(HijosError):
    pass


class DuplicateHijoError(HijosError):
    pass
