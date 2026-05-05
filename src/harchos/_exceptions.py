"""HarchOS SDK exception hierarchy.

All exceptions inherit from :class:`HarchOSError` for easy catch-all
handling. Each error carries a machine-readable ``code``, a human-readable
``title`` and ``detail``, plus a ``doc_url`` pointing to remediation docs.

Example::

    try:
        client.inference.chat.completions.create(...)
    except harchos.RateLimitError as e:
        print(e.code)      # "E0429"
        print(e.title)     # "Rate limit exceeded"
        print(e.doc_url)   # "https://docs.harchos.ai/errors/E0429"
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class HarchOSError(Exception):
    """Base exception for all HarchOS SDK errors.

    Attributes:
        code: Machine-readable error code (e.g. ``"E0400"``).
        title: Short human-readable title.
        detail: Longer human-readable description.
        doc_url: URL to the error documentation page.
        status_code: HTTP status code that triggered this error (if any).
        headers: HTTP response headers.
        body: Raw response body.
    """

    def __init__(
        self,
        message: str = "An unknown error occurred",
        *,
        code: str = "E0000",
        title: str = "Unknown Error",
        detail: Optional[str] = None,
        doc_url: Optional[str] = None,
        status_code: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.title = title
        self.detail = detail or message
        self.doc_url = doc_url
        self.status_code = status_code
        self.headers = headers or {}
        self.body = body

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code!r}, title={self.title!r})"

    def __str__(self) -> str:
        parts = [f"[{self.code}]", self.title]
        if self.detail and self.detail != self.title:
            parts.append(f"— {self.detail}")
        return " ".join(parts)


class AuthenticationError(HarchOSError):
    """Raised on invalid or missing credentials (HTTP 401).

    Code: ``E0401``
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("code", "E0401")
        kwargs.setdefault("title", "Authentication Error")
        kwargs.setdefault("doc_url", "https://docs.harchos.ai/errors/E0401")
        kwargs.setdefault("status_code", 401)
        super().__init__(message, **kwargs)


class RateLimitError(HarchOSError):
    """Raised when the API rate limit is exceeded (HTTP 429).

    Code: ``E0429``

    Attributes:
        retry_after: Suggested seconds to wait before retrying.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("code", "E0429")
        kwargs.setdefault("title", "Rate Limit Error")
        kwargs.setdefault("doc_url", "https://docs.harchos.ai/errors/E0429")
        kwargs.setdefault("status_code", 429)
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class NotFoundError(HarchOSError):
    """Raised when a resource is not found (HTTP 404).

    Code: ``E0404``
    """

    def __init__(
        self,
        message: str = "Resource not found",
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("code", "E0404")
        kwargs.setdefault("title", "Not Found")
        kwargs.setdefault("doc_url", "https://docs.harchos.ai/errors/E0404")
        kwargs.setdefault("status_code", 404)
        super().__init__(message, **kwargs)


class ValidationError(HarchOSError):
    """Raised when request validation fails (HTTP 400/422).

    Code: ``E0400``
    """

    def __init__(
        self,
        message: str = "Validation error",
        *,
        field: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("code", "E0400")
        kwargs.setdefault("title", "Validation Error")
        kwargs.setdefault("doc_url", "https://docs.harchos.ai/errors/E0400")
        kwargs.setdefault("status_code", 400)
        super().__init__(message, **kwargs)
        self.field = field


class InferenceError(HarchOSError):
    """Raised when an inference request fails at the model level.

    Code: ``E0500``
    """

    def __init__(
        self,
        message: str = "Inference failed",
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("code", "E0500")
        kwargs.setdefault("title", "Inference Error")
        kwargs.setdefault("doc_url", "https://docs.harchos.ai/errors/E0500")
        kwargs.setdefault("status_code", 500)
        super().__init__(message, **kwargs)


# ---------------------------------------------------------------------------
# Status-code → exception mapping
# ---------------------------------------------------------------------------

_STATUS_CODE_MAP: Dict[int, type[HarchOSError]] = {
    400: ValidationError,
    401: AuthenticationError,
    404: NotFoundError,
    422: ValidationError,
    429: RateLimitError,
    500: InferenceError,
}


def make_error(
    status_code: int,
    *,
    message: Optional[str] = None,
    body: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None,
) -> HarchOSError:
    """Construct the appropriate typed error from an HTTP status code.

    Tries to parse structured error fields (``code``, ``title``, ``detail``,
    ``doc_url``) from the response body before falling back to defaults.

    Args:
        status_code: HTTP status code.
        message: Default message if body parsing fails.
        body: Parsed response body (dict) or raw text.
        headers: Response headers.

    Returns:
        An instance of the appropriate :class:`HarchOSError` subclass.
    """
    error_cls = _STATUS_CODE_MAP.get(status_code, HarchOSError)
    default_msg = f"HTTP {status_code}"

    # Try to extract structured error from body
    code: Optional[str] = None
    title: Optional[str] = None
    detail: Optional[str] = None
    doc_url: Optional[str] = None

    if isinstance(body, dict):
        # Support both {error: {...}} and flat {code, title, ...}
        err = body.get("error", body)
        if isinstance(err, dict):
            code = err.get("code")
            title = err.get("title") or err.get("message")
            detail = err.get("detail") or err.get("message")
            doc_url = err.get("doc_url") or err.get("docUrl")

    kwargs: Dict[str, Any] = {
        "status_code": status_code,
        "headers": headers,
        "body": body,
    }
    if code:
        kwargs["code"] = code
    if title:
        kwargs["title"] = title
    if detail:
        kwargs["detail"] = detail
    if doc_url:
        kwargs["doc_url"] = doc_url

    # Special: 429 Retry-After
    if status_code == 429 and headers:
        retry_after = headers.get("retry-after") or headers.get("Retry-After")
        if retry_after:
            try:
                kwargs["retry_after"] = float(retry_after)
            except ValueError:
                pass

    return error_cls(message or default_msg, **kwargs)
