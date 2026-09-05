"""Domain errors raised by point persistence operations."""


class PointNotFoundError(Exception):
    """Raised when a requested point does not exist."""


class PointOrderConflictError(Exception):
    """Raised when a reorder request contains a stale point set."""
