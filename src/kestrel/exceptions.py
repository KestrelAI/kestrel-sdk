class KestrelError(Exception):
    """Base exception for Kestrel SDK errors."""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class AuthError(KestrelError):
    """Authentication failed or session expired."""


class NotFoundError(KestrelError):
    """Requested resource was not found."""


class ConflictError(KestrelError):
    """Resource already exists (e.g. duplicate workflow name)."""


class ServerError(KestrelError):
    """Server returned an unexpected error."""
