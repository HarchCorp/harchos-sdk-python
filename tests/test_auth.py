"""Tests for the HarchOS authentication module."""

from __future__ import annotations

import os
import time
from unittest.mock import patch

import pytest

from harchos.auth import Authenticator
from harchos.errors import APIKeyExpiredError, InvalidAPIKeyError


class TestAuthenticatorInit:
    """Tests for Authenticator initialization."""

    def test_with_api_key(self) -> None:
        auth = Authenticator(api_key="hsk_testapikey1234567890")
        assert auth.api_key == "hsk_testapikey1234567890"

    def test_with_token(self) -> None:
        auth = Authenticator(token="hst_sometoken123")
        assert auth.token == "hst_sometoken123"

    def test_empty(self) -> None:
        auth = Authenticator()
        assert auth.api_key is None
        assert auth.token is None

    def test_invalid_key_prefix(self) -> None:
        with pytest.raises(InvalidAPIKeyError, match="must start with"):
            Authenticator(api_key="invalid_key_1234567890")

    def test_key_too_short(self) -> None:
        with pytest.raises(InvalidAPIKeyError, match="at least"):
            Authenticator(api_key="hsk_short")

    def test_empty_key(self) -> None:
        with pytest.raises(InvalidAPIKeyError, match="must not be empty"):
            Authenticator(api_key="   ")


class TestSetAPIKey:
    """Tests for set_api_key method."""

    def test_valid_key(self) -> None:
        auth = Authenticator()
        auth.set_api_key("hsk_anotherkey1234567890")
        assert auth.api_key == "hsk_anotherkey1234567890"

    def test_strips_whitespace(self) -> None:
        auth = Authenticator()
        auth.set_api_key("  hsk_anotherkey1234567890  ")
        assert auth.api_key == "hsk_anotherkey1234567890"

    def test_invalid_format(self) -> None:
        auth = Authenticator()
        with pytest.raises(InvalidAPIKeyError):
            auth.set_api_key("bad_key")


class TestTokenManagement:
    """Tests for token management."""

    def test_set_token_with_expires_at(self) -> None:
        auth = Authenticator()
        expires = time.time() + 3600
        auth.set_token("hst_token123", expires_at=expires)
        assert auth.token == "hst_token123"
        assert auth._token_expires_at == expires

    def test_set_token_with_ttl(self) -> None:
        auth = Authenticator()
        before = time.time()
        auth.set_token("hst_token123", ttl=600)
        after = time.time()
        assert auth._token_expires_at is not None
        assert before + 600 <= auth._token_expires_at <= after + 600

    def test_cannot_set_both_expires_and_ttl(self) -> None:
        auth = Authenticator()
        with pytest.raises(ValueError, match="not both"):
            auth.set_token("hst_token123", expires_at=1000.0, ttl=600)

    def test_is_token_expired_no_token(self) -> None:
        auth = Authenticator()
        assert auth.is_token_expired is True

    def test_is_token_expired_future(self) -> None:
        auth = Authenticator()
        auth.set_token("hst_token123", ttl=3600)
        assert auth.is_token_expired is False

    def test_is_token_expired_past(self) -> None:
        auth = Authenticator()
        auth.set_token("hst_token123", expires_at=time.time() - 100)
        assert auth.is_token_expired is True

    def test_clear_token(self) -> None:
        auth = Authenticator()
        auth.set_token("hst_token123", ttl=3600)
        auth.clear_token()
        assert auth.token is None
        assert auth._token_expires_at is None


class TestGetHeaders:
    """Tests for header construction."""

    def test_api_key_header(self) -> None:
        auth = Authenticator(api_key="hsk_testapikey1234567890")
        headers = auth.get_headers()
        assert headers["X-API-Key"] == "hsk_testapikey1234567890"

    def test_token_header(self) -> None:
        auth = Authenticator(api_key="hsk_testapikey1234567890")
        auth.set_token("hst_token123", ttl=3600)
        headers = auth.get_headers()
        assert headers["Authorization"] == "Bearer hst_token123"
        assert "X-API-Key" not in headers

    def test_expired_token_falls_back_to_key(self) -> None:
        auth = Authenticator(api_key="hsk_testapikey1234567890")
        auth.set_token("hst_token123", expires_at=time.time() - 100)
        headers = auth.get_headers()
        assert headers["X-API-Key"] == "hsk_testapikey1234567890"

    def test_expired_token_no_key_raises(self) -> None:
        auth = Authenticator()
        auth.set_token("hst_token123", expires_at=time.time() - 100)
        with pytest.raises(APIKeyExpiredError):
            auth.get_headers()

    def test_no_credentials_empty_headers(self) -> None:
        auth = Authenticator()
        headers = auth.get_headers()
        assert headers == {}

    def test_token_preferred_over_key(self) -> None:
        auth = Authenticator(api_key="hsk_testapikey1234567890")
        auth.set_token("hst_token123", ttl=3600)
        headers = auth.get_headers()
        assert "Authorization" in headers
        assert "X-API-Key" not in headers


class TestRepr:
    """Tests for Authenticator.__repr__."""

    def test_repr_with_key(self) -> None:
        auth = Authenticator(api_key="hsk_testapikey1234567890")
        r = repr(auth)
        assert "Authenticator" in r
        assert "hsk_test" in r
        assert "7890" in r

    def test_repr_with_token(self) -> None:
        auth = Authenticator(token="hst_token123")
        r = repr(auth)
        assert "token=***" in r


class TestFromEnv:
    """Tests for Authenticator.from_env class method."""

    def test_from_env_with_key(self, clean_env: None) -> None:
        os.environ["HARCHOS_API_KEY"] = "hsk_envtestkey123456789"
        auth = Authenticator.from_env()
        assert auth.api_key == "hsk_envtestkey123456789"

    def test_from_env_without_key(self, clean_env: None) -> None:
        auth = Authenticator.from_env()
        assert auth.api_key is None
