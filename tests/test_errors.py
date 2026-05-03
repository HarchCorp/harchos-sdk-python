"""Tests for the HarchOS error hierarchy."""

from __future__ import annotations

import pytest

from harchos.errors import (
    APIKeyExpiredError,
    AuthenticationError,
    BadRequestError,
    CarbonBudgetExceededError,
    ConflictError,
    ConnectionError,
    DataResidencyError,
    ForbiddenError,
    HarchOSError,
    InternalServerError,
    InvalidAPIKeyError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServiceUnavailableError,
    SovereigntyError,
    TimeoutError,
    UnauthorizedError,
    ValidationError,
    raise_for_status,
)


class TestHarchOSError:
    """Tests for the base HarchOSError class."""

    def test_default_message(self) -> None:
        err = HarchOSError()
        assert err.message == "An unknown error occurred"
        assert err.code is None
        assert err.status_code is None

    def test_custom_message(self) -> None:
        err = HarchOSError("Something went wrong")
        assert str(err) == "Something went wrong"

    def test_with_code(self) -> None:
        err = HarchOSError("Bad stuff", code="bad_stuff")
        assert str(err) == "[bad_stuff] Bad stuff"

    def test_with_status_code(self) -> None:
        err = HarchOSError("Not found", code="not_found", status_code=404)
        assert err.status_code == 404

    def test_with_headers_and_body(self) -> None:
        err = HarchOSError(
            "Error",
            headers={"X-Request-Id": "abc"},
            body={"detail": "info"},
        )
        assert err.headers["X-Request-Id"] == "abc"
        assert err.body == {"detail": "info"}

    def test_repr(self) -> None:
        err = HarchOSError("Test", code="test_code", status_code=500)
        r = repr(err)
        assert "HarchOSError" in r
        assert "test_code" in r
        assert "500" in r

    def test_is_exception(self) -> None:
        with pytest.raises(HarchOSError):
            raise HarchOSError("test")


class TestErrorHierarchy:
    """Test that the error inheritance is correct."""

    def test_authentication_errors(self) -> None:
        assert issubclass(APIKeyExpiredError, AuthenticationError)
        assert issubclass(InvalidAPIKeyError, AuthenticationError)
        assert issubclass(PermissionDeniedError, AuthenticationError)
        assert issubclass(AuthenticationError, HarchOSError)

    def test_sovereignty_errors(self) -> None:
        assert issubclass(DataResidencyError, SovereigntyError)
        assert issubclass(CarbonBudgetExceededError, SovereigntyError)
        assert issubclass(SovereigntyError, HarchOSError)

    def test_http_errors(self) -> None:
        assert issubclass(BadRequestError, HarchOSError)
        assert issubclass(UnauthorizedError, AuthenticationError)
        assert issubclass(ForbiddenError, HarchOSError)
        assert issubclass(NotFoundError, HarchOSError)
        assert issubclass(ConflictError, HarchOSError)
        assert issubclass(RateLimitError, HarchOSError)
        assert issubclass(InternalServerError, HarchOSError)

    def test_api_key_expired_defaults(self) -> None:
        err = APIKeyExpiredError()
        assert err.code == "api_key_expired"

    def test_invalid_api_key_defaults(self) -> None:
        err = InvalidAPIKeyError()
        assert err.code == "invalid_api_key"

    def test_permission_denied_defaults(self) -> None:
        err = PermissionDeniedError()
        assert err.code == "permission_denied"


class TestRateLimitError:
    """Tests for RateLimitError specific behaviour."""

    def test_retry_after(self) -> None:
        err = RateLimitError(retry_after=5.0)
        assert err.retry_after == 5.0
        assert err.status_code == 429

    def test_no_retry_after(self) -> None:
        err = RateLimitError()
        assert err.retry_after is None


class TestCarbonBudgetExceededError:
    """Tests for CarbonBudgetExceededError."""

    def test_with_budget_info(self) -> None:
        err = CarbonBudgetExceededError(
            budget_grams=1000.0,
            actual_grams=1200.0,
        )
        assert err.budget_grams == 1000.0
        assert err.actual_grams == 1200.0

    def test_defaults(self) -> None:
        err = CarbonBudgetExceededError()
        assert err.budget_grams is None
        assert err.actual_grams is None


class TestDataResidencyError:
    """Tests for DataResidencyError."""

    def test_with_regions(self) -> None:
        err = DataResidencyError(
            required_region="morocco",
            actual_region="us_east",
        )
        assert err.required_region == "morocco"
        assert err.actual_region == "us_east"


class TestValidationError:
    """Tests for ValidationError."""

    def test_with_field(self) -> None:
        err = ValidationError(field="name")
        assert err.field == "name"


class TestRaiseForStatus:
    """Tests for the raise_for_status helper."""

    def test_success_codes(self) -> None:
        # Should not raise for 2xx codes
        raise_for_status(200, "OK")
        raise_for_status(201, "Created")
        raise_for_status(204, "No Content")

    def test_400_raises_bad_request(self) -> None:
        with pytest.raises(BadRequestError):
            raise_for_status(400, "Bad request")

    def test_401_raises_unauthorized(self) -> None:
        with pytest.raises(UnauthorizedError):
            raise_for_status(401, "Unauthorized")

    def test_403_raises_forbidden(self) -> None:
        with pytest.raises(ForbiddenError):
            raise_for_status(403, "Forbidden")

    def test_404_raises_not_found(self) -> None:
        with pytest.raises(NotFoundError):
            raise_for_status(404, "Not found")

    def test_429_raises_rate_limit(self) -> None:
        with pytest.raises(RateLimitError):
            raise_for_status(429, "Too many requests")

    def test_429_extracts_retry_after(self) -> None:
        with pytest.raises(RateLimitError) as exc_info:
            raise_for_status(
                429,
                "Too many requests",
                headers={"Retry-After": "30"},
            )
        assert exc_info.value.retry_after == 30.0

    def test_500_raises_internal_server_error(self) -> None:
        with pytest.raises(InternalServerError):
            raise_for_status(500, "Internal server error")

    def test_503_raises_service_unavailable(self) -> None:
        with pytest.raises(ServiceUnavailableError):
            raise_for_status(503, "Service unavailable")

    def test_unknown_status_raises_base(self) -> None:
        with pytest.raises(HarchOSError):
            raise_for_status(418, "I'm a teapot")

    def test_passes_headers_and_body(self) -> None:
        with pytest.raises(NotFoundError) as exc_info:
            raise_for_status(
                404,
                "Not found",
                headers={"X-Request-Id": "req123"},
                body={"error": "resource missing"},
            )
        assert exc_info.value.headers["X-Request-Id"] == "req123"
        assert exc_info.value.body == {"error": "resource missing"}
