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


class ValidationError(KestrelError):
    """Workflow validation failed (e.g. missing required fields).

    Attributes:
        missing_fields: List of dicts describing each missing required field.
            Each dict has keys: node_id, node_label, field_name, field_label.
    """

    def __init__(self, message: str, missing_fields: list[dict] | None = None, status_code: int | None = None):
        self.missing_fields = missing_fields or []
        super().__init__(message, status_code)


class ServerError(KestrelError):
    """Server returned an unexpected error."""
