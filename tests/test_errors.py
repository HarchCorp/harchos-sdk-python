"""Tests for the HarchOS exception hierarchy (v0.3)."""

from __future__ import annotations

import pytest

from harchos._exceptions import (
    AuthenticationError,
    HarchOSError,
    InferenceError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    make_error,
)


class TestHarchOSError:
    """Tests for the base HarchOSError class."""

    def test_default_message(self) -> None:
        err = HarchOSError()
        assert err.message == "An unknown error occurred"
        assert err.code == "E0000"
        assert err.title == "Unknown Error"
        assert err.status_code is None
        assert err.headers == {}
        assert err.body is None

    def test_custom_message(self) -> None:
        err = HarchOSError("Something went wrong")
        assert err.message == "Something went wrong"
        assert str(err) == "[E0000] Unknown Error — Something went wrong"

    def test_with_code(self) -> None:
        err = HarchOSError("Bad stuff", code="bad_stuff", title="Bad Stuff")
        assert err.code == "bad_stuff"
        assert err.title == "Bad Stuff"

    def test_with_status_code(self) -> None:
        err = HarchOSError("Not found", status_code=404)
        assert err.status_code == 404

    def test_with_headers_and_body(self) -> None:
        err = HarchOSError(
            "Error",
            headers={"X-Request-Id": "abc"},
            body={"detail": "info"},
        )
        assert err.headers["X-Request-Id"] == "abc"
        assert err.body == {"detail": "info"}

    def test_detail_defaults_to_message(self) -> None:
        err = HarchOSError("Something broke")
        assert err.detail == "Something broke"

    def test_custom_detail(self) -> None:
        err = HarchOSError("Short", detail="A longer explanation of the error")
        assert err.detail == "A longer explanation of the error"

    def test_doc_url(self) -> None:
        err = HarchOSError("Test", doc_url="https://docs.harchos.ai/errors/E0001")
        assert err.doc_url == "https://docs.harchos.ai/errors/E0001"

    def test_repr(self) -> None:
        err = HarchOSError("Test", code="test_code", title="Test Title")
        r = repr(err)
        assert "HarchOSError" in r
        assert "test_code" in r
        assert "Test Title" in r

    def test_is_exception(self) -> None:
        with pytest.raises(HarchOSError):
            raise HarchOSError("test")

    def test_str_format(self) -> None:
        err = HarchOSError("msg", code="E0400", title="Validation Error")
        s = str(err)
        assert "[E0400]" in s
        assert "Validation Error" in s


class TestErrorHierarchy:
    """Test that the error inheritance is correct."""

    def test_authentication_error_inherits(self) -> None:
        assert issubclass(AuthenticationError, HarchOSError)

    def test_rate_limit_error_inherits(self) -> None:
        assert issubclass(RateLimitError, HarchOSError)

    def test_not_found_error_inherits(self) -> None:
        assert issubclass(NotFoundError, HarchOSError)

    def test_validation_error_inherits(self) -> None:
        assert issubclass(ValidationError, HarchOSError)

    def test_inference_error_inherits(self) -> None:
        assert issubclass(InferenceError, HarchOSError)

    def test_all_catchable_by_base(self) -> None:
        for exc_cls in [AuthenticationError, RateLimitError, NotFoundError,
                        ValidationError, InferenceError]:
            with pytest.raises(HarchOSError):
                raise exc_cls()


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_defaults(self) -> None:
        err = AuthenticationError()
        assert err.code == "E0401"
        assert err.title == "Authentication Error"
        assert err.status_code == 401
        assert err.doc_url == "https://docs.harchos.ai/errors/E0401"

    def test_custom_message(self) -> None:
        err = AuthenticationError("Invalid API key")
        assert err.message == "Invalid API key"
        assert err.status_code == 401

    def test_override_default_code(self) -> None:
        err = AuthenticationError("test", code="CUSTOM")
        assert err.code == "CUSTOM"


class TestRateLimitError:
    """Tests for RateLimitError specific behaviour."""

    def test_defaults(self) -> None:
        err = RateLimitError()
        assert err.code == "E0429"
        assert err.title == "Rate Limit Error"
        assert err.status_code == 429
        assert err.retry_after is None

    def test_retry_after(self) -> None:
        err = RateLimitError(retry_after=5.0)
        assert err.retry_after == 5.0
        assert err.status_code == 429


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_defaults(self) -> None:
        err = NotFoundError()
        assert err.code == "E0404"
        assert err.title == "Not Found"
        assert err.status_code == 404

    def test_custom_message(self) -> None:
        err = NotFoundError("Hub not found")
        assert err.message == "Hub not found"


class TestValidationError:
    """Tests for ValidationError."""

    def test_defaults(self) -> None:
        err = ValidationError()
        assert err.code == "E0400"
        assert err.title == "Validation Error"
        assert err.status_code == 400
        assert err.field is None

    def test_with_field(self) -> None:
        err = ValidationError(field="name")
        assert err.field == "name"


class TestInferenceError:
    """Tests for InferenceError."""

    def test_defaults(self) -> None:
        err = InferenceError()
        assert err.code == "E0500"
        assert err.title == "Inference Error"
        assert err.status_code == 500

    def test_custom_message(self) -> None:
        err = InferenceError("Model unavailable")
        assert err.message == "Model unavailable"


class TestMakeError:
    """Tests for the make_error factory function."""

    def test_400_returns_validation_error(self) -> None:
        err = make_error(400, message="Bad request")
        assert isinstance(err, ValidationError)
        assert err.status_code == 400

    def test_401_returns_authentication_error(self) -> None:
        err = make_error(401, message="Unauthorized")
        assert isinstance(err, AuthenticationError)
        assert err.status_code == 401

    def test_404_returns_not_found_error(self) -> None:
        err = make_error(404, message="Not found")
        assert isinstance(err, NotFoundError)
        assert err.status_code == 404

    def test_422_returns_validation_error(self) -> None:
        err = make_error(422, message="Unprocessable")
        assert isinstance(err, ValidationError)
        assert err.status_code == 422

    def test_429_returns_rate_limit_error(self) -> None:
        err = make_error(429, message="Too many requests")
        assert isinstance(err, RateLimitError)
        assert err.status_code == 429

    def test_429_extracts_retry_after(self) -> None:
        err = make_error(
            429,
            message="Too many requests",
            headers={"retry-after": "30"},
        )
        assert isinstance(err, RateLimitError)
        assert err.retry_after == 30.0

    def test_500_returns_inference_error(self) -> None:
        err = make_error(500, message="Internal server error")
        assert isinstance(err, InferenceError)
        assert err.status_code == 500

    def test_unknown_status_returns_base_error(self) -> None:
        err = make_error(418, message="I'm a teapot")
        assert isinstance(err, HarchOSError)
        assert not isinstance(err, AuthenticationError)
        assert err.status_code == 418

    def test_extracts_structured_error_from_body(self) -> None:
        err = make_error(
            400,
            message="Bad request",
            body={"error": {"code": "E0401", "title": "Custom Title", "detail": "Custom detail"}},
        )
        assert err.code == "E0401"
        assert err.title == "Custom Title"
        assert err.detail == "Custom detail"

    def test_extracts_flat_error_from_body(self) -> None:
        err = make_error(
            400,
            message="Bad request",
            body={"code": "CUSTOM_CODE", "title": "Flat Title"},
        )
        assert err.code == "CUSTOM_CODE"
        assert err.title == "Flat Title"

    def test_passes_headers_and_body(self) -> None:
        err = make_error(
            404,
            message="Not found",
            headers={"X-Request-Id": "req123"},
            body={"error": "resource missing"},
        )
        assert err.headers["X-Request-Id"] == "req123"
        assert err.body == {"error": "resource missing"}

    def test_default_message_from_status_code(self) -> None:
        err = make_error(500)
        assert err.message == "HTTP 500"
