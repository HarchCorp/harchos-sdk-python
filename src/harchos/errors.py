"""HarchOS SDK error hierarchy.

Provides a comprehensive set of typed exceptions for all error conditions
encountered when interacting with the HarchOS API. All exceptions inherit
from :class:`HarchOSError` for easy catch-all handling.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class HarchOSError(Exception):
    """Base exception for all HarchOS SDK errors.

    Attributes:
        message: Human-readable error description.
        code: Machine-readable error code returned by the API (if any).
        status_code: HTTP status code that triggered the error (if applicable).
        headers: HTTP response headers associated with the error.
        body: Raw response body for advanced debugging.
    """

    def __init__(
        self,
        message: str = "An unknown error occurred",
        *,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.headers = headers or {}
        self.body = body
        super().__init__(message)

    def __repr__(self) -> str:
        parts = [self.__class__.__name__]
        if self.code:
            parts.append(f"code={self.code!r}")
        if self.status_code:
            parts.append(f"status_code={self.status_code}")
        return f"{'('.join(parts)})" if len(parts) > 1 else parts[0]

    def __str__(self) -> str:
        prefix = f"[{self.code}] " if self.code else ""
        return f"{prefix}{self.message}"


# ---------------------------------------------------------------------------
# Authentication errors
# ---------------------------------------------------------------------------

class AuthenticationError(HarchOSError):
    """Raised when authentication fails (invalid key, expired token, etc.)."""


class APIKeyExpiredError(AuthenticationError):
    """Raised when the API key has expired."""

    def __init__(self, message: str = "API key has expired", **kwargs: Any) -> None:
        super().__init__(message, code="api_key_expired", **kwargs)


class InvalidAPIKeyError(AuthenticationError):
    """Raised when the provided API key is invalid."""

    def __init__(self, message: str = "Invalid API key", **kwargs: Any) -> None:
        super().__init__(message, code="invalid_api_key", **kwargs)


class PermissionDeniedError(AuthenticationError):
    """Raised when the authenticated principal lacks required permissions."""

    def __init__(self, message: str = "Permission denied", **kwargs: Any) -> None:
        super().__init__(message, code="permission_denied", **kwargs)


# ---------------------------------------------------------------------------
# Connection / network errors
# ---------------------------------------------------------------------------

class ConnectionError(HarchOSError):
    """Raised when a network-level connection failure occurs."""

    def __init__(self, message: str = "Connection failed", **kwargs: Any) -> None:
        super().__init__(message, code="connection_error", **kwargs)


class TimeoutError(HarchOSError):
    """Raised when an API request exceeds the configured timeout."""

    def __init__(self, message: str = "Request timed out", **kwargs: Any) -> None:
        super().__init__(message, code="timeout", **kwargs)


class ServiceUnavailableError(HarchOSError):
    """Raised when the HarchOS API returns 503."""

    def __init__(
        self, message: str = "Service temporarily unavailable", **kwargs: Any
    ) -> None:
        super().__init__(message, code="service_unavailable", **kwargs)


# ---------------------------------------------------------------------------
# HTTP status-mapped errors
# ---------------------------------------------------------------------------

class BadRequestError(HarchOSError):
    """Raised when the API returns HTTP 400."""

    def __init__(self, message: str = "Bad request", **kwargs: Any) -> None:
        super().__init__(message, code="bad_request", status_code=400, **kwargs)


class UnauthorizedError(AuthenticationError):
    """Raised when the API returns HTTP 401."""

    def __init__(self, message: str = "Unauthorized", **kwargs: Any) -> None:
        super().__init__(message, code="unauthorized", status_code=401, **kwargs)


class ForbiddenError(HarchOSError):
    """Raised when the API returns HTTP 403."""

    def __init__(self, message: str = "Forbidden", **kwargs: Any) -> None:
        super().__init__(message, code="forbidden", status_code=403, **kwargs)


class NotFoundError(HarchOSError):
    """Raised when the requested resource does not exist (HTTP 404)."""

    def __init__(self, message: str = "Resource not found", **kwargs: Any) -> None:
        super().__init__(message, code="not_found", status_code=404, **kwargs)


class ConflictError(HarchOSError):
    """Raised when a conflict prevents the operation (HTTP 409)."""

    def __init__(self, message: str = "Conflict", **kwargs: Any) -> None:
        super().__init__(message, code="conflict", status_code=409, **kwargs)


class RateLimitError(HarchOSError):
    """Raised when the API rate limit has been exceeded (HTTP 429).

    Attributes:
        retry_after: Suggested number of seconds to wait before retrying.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, code="rate_limit", status_code=429, **kwargs)


class InternalServerError(HarchOSError):
    """Raised when the API returns HTTP 500."""

    def __init__(
        self, message: str = "Internal server error", **kwargs: Any
    ) -> None:
        super().__init__(message, code="internal_server_error", status_code=500, **kwargs)


# ---------------------------------------------------------------------------
# Sovereignty & compliance errors
# ---------------------------------------------------------------------------

class SovereigntyError(HarchOSError):
    """Raised when an operation violates data sovereignty constraints."""

    def __init__(
        self,
        message: str = "Operation violates sovereignty constraints",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code="sovereignty_violation", **kwargs)


class DataResidencyError(SovereigntyError):
    """Raised when data would be stored outside the required jurisdiction."""

    def __init__(
        self,
        message: str = "Data residency constraint violated",
        *,
        required_region: Optional[str] = None,
        actual_region: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.required_region = required_region
        self.actual_region = actual_region
        super().__init__(message, code="data_residency_violation", **kwargs)


class CarbonBudgetExceededError(SovereigntyError):
    """Raised when an operation would exceed the carbon budget."""

    def __init__(
        self,
        message: str = "Carbon budget exceeded",
        *,
        budget_grams: Optional[float] = None,
        actual_grams: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        self.budget_grams = budget_grams
        self.actual_grams = actual_grams
        super().__init__(message, code="carbon_budget_exceeded", **kwargs)


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

class ValidationError(HarchOSError):
    """Raised when request data fails validation before sending to the API."""

    def __init__(
        self,
        message: str = "Validation error",
        *,
        field: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.field = field
        super().__init__(message, code="validation_error", **kwargs)


# ---------------------------------------------------------------------------
# Mapping helper
# ---------------------------------------------------------------------------

_STATUS_CODE_MAP: Dict[int, type[HarchOSError]] = {
    400: BadRequestError,
    401: UnauthorizedError,
    403: ForbiddenError,
    404: NotFoundError,
    409: ConflictError,
    429: RateLimitError,
    500: InternalServerError,
    503: ServiceUnavailableError,
}


def raise_for_status(
    status_code: int,
    message: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    body: Optional[Any] = None,
) -> None:
    """Raise the appropriate :class:`HarchOSError` subclass for *status_code*.

    If *status_code* is not in the known mapping, a generic
    :class:`HarchOSError` is raised with the status code attached.

    Args:
        status_code: HTTP response status code.
        message: Error message from the response body.
        headers: Response headers (used e.g. for ``Retry-After``).
        body: Raw response body.

    Raises:
        HarchOSError: The typed exception matching *status_code*.
    """
    if 200 <= status_code < 300:
        return

    error_cls = _STATUS_CODE_MAP.get(status_code, HarchOSError)

    kwargs: Dict[str, Any] = {
        "status_code": status_code,
        "headers": headers,
        "body": body,
    }

    # Special handling for 429 – extract Retry-After header
    if status_code == 429 and headers:
        retry_after_str = headers.get("retry-after") or headers.get("Retry-After")
        if retry_after_str:
            try:
                kwargs["retry_after"] = float(retry_after_str)
            except ValueError:
                pass

    raise error_cls(message, **kwargs)
