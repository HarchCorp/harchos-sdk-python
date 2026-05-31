"""Tests for the HarchOS Config class (v0.3)."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from harchos._config import Config, DEFAULT_BASE_URL, DEFAULT_TIMEOUT, DEFAULT_MAX_RETRIES


class TestConfigDefaults:
    """Tests for Config default values."""

    def test_default_base_url(self, clean_env: None) -> None:
        config = Config()
        assert config.base_url == DEFAULT_BASE_URL
        assert config.base_url == "https://api.harchos.ai/v1"

    def test_default_timeout(self, clean_env: None) -> None:
        config = Config()
        assert config.timeout == DEFAULT_TIMEOUT
        assert config.timeout == 30.0

    def test_default_max_retries(self, clean_env: None) -> None:
        config = Config()
        assert config.max_retries == DEFAULT_MAX_RETRIES
        assert config.max_retries == 3

    def test_default_api_key_is_none(self, clean_env: None) -> None:
        config = Config()
        assert config.api_key is None

    def test_default_headers_is_empty_dict(self, clean_env: None) -> None:
        config = Config()
        assert config.default_headers == {}


class TestConfigCustomValues:
    """Tests for Config with custom values."""

    def test_custom_api_key(self) -> None:
        config = Config(api_key="hsk_testkey1234567890")
        assert config.api_key == "hsk_testkey1234567890"

    def test_custom_base_url(self) -> None:
        config = Config(base_url="https://custom.api.com/v1")
        assert config.base_url == "https://custom.api.com/v1"

    def test_custom_timeout(self) -> None:
        config = Config(timeout=60.0)
        assert config.timeout == 60.0

    def test_custom_max_retries(self) -> None:
        config = Config(max_retries=5)
        assert config.max_retries == 5

    def test_custom_default_headers(self) -> None:
        headers = {"X-Custom": "value", "X-Another": "test"}
        config = Config(default_headers=headers)
        assert config.default_headers == headers

    def test_all_custom(self) -> None:
        config = Config(
            api_key="hsk_testkey1234567890",
            base_url="https://custom.api.com/v1",
            timeout=60.0,
            max_retries=5,
            default_headers={"X-Custom": "value"},
        )
        assert config.api_key == "hsk_testkey1234567890"
        assert config.base_url == "https://custom.api.com/v1"
        assert config.timeout == 60.0
        assert config.max_retries == 5
        assert config.default_headers == {"X-Custom": "value"}


class TestConfigNormalization:
    """Tests for Config value normalization."""

    def test_base_url_trailing_slash_stripped(self) -> None:
        config = Config(base_url="https://api.harchos.ai/v1/")
        assert config.base_url == "https://api.harchos.ai/v1"

    def test_base_url_multiple_trailing_slashes(self) -> None:
        config = Config(base_url="https://api.harchos.ai/v1///")
        assert config.base_url == "https://api.harchos.ai/v1"

    def test_api_key_strip_whitespace(self, clean_env: None) -> None:
        config = Config(api_key="  hsk_testkey1234567890  ")
        assert config.api_key == "hsk_testkey1234567890"

    def test_api_key_none_stays_none(self, clean_env: None) -> None:
        config = Config(api_key=None)
        assert config.api_key is None

    def test_api_key_whitespace_only_becomes_empty(self, clean_env: None) -> None:
        config = Config(api_key="   ")
        assert config.api_key == ""

    def test_max_retries_clamped_lower(self) -> None:
        config = Config(max_retries=-1)
        assert config.max_retries == 0

    def test_max_retries_clamped_upper(self) -> None:
        config = Config(max_retries=15)
        assert config.max_retries == 10

    def test_max_retries_zero_allowed(self) -> None:
        config = Config(max_retries=0)
        assert config.max_retries == 0

    def test_max_retries_ten_allowed(self) -> None:
        config = Config(max_retries=10)
        assert config.max_retries == 10


class TestConfigFromEnv:
    """Tests for Config.from_env class method."""

    def test_from_env_api_key(self, clean_env: None) -> None:
        os.environ["HARCHOS_API_KEY"] = "hsk_envkey1234567890"
        config = Config.from_env()
        assert config.api_key == "hsk_envkey1234567890"

    def test_from_env_base_url(self, clean_env: None) -> None:
        os.environ["HARCHOS_BASE_URL"] = "https://staging.api.harchos.ai/v1"
        config = Config.from_env()
        assert config.base_url == "https://staging.api.harchos.ai/v1"

    def test_from_env_timeout(self, clean_env: None) -> None:
        os.environ["HARCHOS_TIMEOUT"] = "45.0"
        config = Config.from_env()
        assert config.timeout == 45.0

    def test_from_env_max_retries(self, clean_env: None) -> None:
        os.environ["HARCHOS_MAX_RETRIES"] = "7"
        config = Config.from_env()
        assert config.max_retries == 7

    def test_from_env_invalid_timeout_ignored(self, clean_env: None) -> None:
        os.environ["HARCHOS_TIMEOUT"] = "not_a_number"
        config = Config.from_env()
        assert config.timeout == DEFAULT_TIMEOUT

    def test_from_env_invalid_max_retries_ignored(self, clean_env: None) -> None:
        os.environ["HARCHOS_MAX_RETRIES"] = "not_a_number"
        config = Config.from_env()
        assert config.max_retries == DEFAULT_MAX_RETRIES

    def test_from_env_with_overrides(self, clean_env: None) -> None:
        os.environ["HARCHOS_API_KEY"] = "hsk_envkey1234567890"
        os.environ["HARCHOS_TIMEOUT"] = "45.0"
        config = Config.from_env(timeout=99.0)
        # Override should take precedence
        assert config.api_key == "hsk_envkey1234567890"
        assert config.timeout == 99.0

    def test_from_env_no_vars_uses_defaults(self, clean_env: None) -> None:
        config = Config.from_env()
        assert config.api_key is None
        assert config.base_url == DEFAULT_BASE_URL
        assert config.timeout == DEFAULT_TIMEOUT
        assert config.max_retries == DEFAULT_MAX_RETRIES


class TestConfigEnvFallback:
    """Tests for Config constructor reading from env when not specified."""

    def test_api_key_from_env(self, clean_env: None) -> None:
        os.environ["HARCHOS_API_KEY"] = "hsk_envkey1234567890"
        config = Config()
        assert config.api_key == "hsk_envkey1234567890"

    def test_explicit_api_key_overrides_env(self, clean_env: None) -> None:
        os.environ["HARCHOS_API_KEY"] = "hsk_envkey1234567890"
        config = Config(api_key="hsk_explicit1234567890")
        assert config.api_key == "hsk_explicit1234567890"


class TestConfigRepr:
    """Tests for Config.__repr__."""

    def test_repr_with_api_key(self) -> None:
        config = Config(api_key="hsk_testapikey1234567890")
        r = repr(config)
        assert "Config" in r
        assert "7890" in r
        # Full key should NOT appear
        assert "hsk_testapikey1234567890" not in r

    def test_repr_without_api_key(self, clean_env: None) -> None:
        config = Config()
        r = repr(config)
        assert "None" in r
        assert "harchos.ai" in r

    def test_repr_shows_base_url(self) -> None:
        config = Config(base_url="https://custom.api.com/v1")
        r = repr(config)
        assert "custom.api.com" in r


class TestConfigSlots:
    """Tests for Config __slots__ behavior."""

    def test_has_expected_slots(self) -> None:
        config = Config()
        assert hasattr(config, "api_key")
        assert hasattr(config, "base_url")
        assert hasattr(config, "timeout")
        assert hasattr(config, "max_retries")
        assert hasattr(config, "default_headers")

    def test_cannot_set_arbitrary_attribute(self) -> None:
        config = Config()
        with pytest.raises(AttributeError):
            config.arbitrary_field = "test"  # type: ignore[attr-defined]
