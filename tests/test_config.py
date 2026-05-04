"""Tests for the HarchOS configuration module."""

from __future__ import annotations

import os
import pathlib
from unittest.mock import patch

import pytest

from harchos.config import (
    HarchOSConfig,
    Profile,
)


class TestHarchOSConfig:
    """Tests for HarchOSConfig."""

    def test_sovereign_defaults(self) -> None:
        config = HarchOSConfig()
        assert config.region == "morocco"
        assert config.sovereignty == "strict"
        assert config.carbon_aware is True
        assert config.base_url == "https://api.harchos.io/v1"
        assert config.timeout == 30.0
        assert config.max_retries == 3

    def test_custom_values(self) -> None:
        config = HarchOSConfig(
            api_key="hsk_testkey1234567890",
            region="uae",
            sovereignty="moderate",
            carbon_aware=False,
            timeout=60.0,
        )
        assert config.region == "uae"
        assert config.sovereignty == "moderate"
        assert config.carbon_aware is False
        assert config.timeout == 60.0

    def test_region_normalization(self) -> None:
        config = HarchOSConfig(region="US East")
        assert config.region == "us_east"

    def test_region_normalization_hyphen(self) -> None:
        config = HarchOSConfig(region="eu-west")
        assert config.region == "eu_west"

    def test_base_url_trailing_slash_stripped(self) -> None:
        config = HarchOSConfig(base_url="https://api.harchos.io/v1/")
        assert config.base_url == "https://api.harchos.io/v1"

    def test_api_key_strip_whitespace(self) -> None:
        config = HarchOSConfig(api_key="  hsk_testkey1234567890  ")
        assert config.api_key == "hsk_testkey1234567890"

    def test_extra_headers(self) -> None:
        config = HarchOSConfig(extra_headers={"X-Custom": "value"})
        assert config.extra_headers["X-Custom"] == "value"

    def test_env_override(self, clean_env: None) -> None:
        os.environ["HARCHOS_REGION"] = "germany"
        os.environ["HARCHOS_TIMEOUT"] = "45.0"
        config = HarchOSConfig()
        assert config.region == "germany"
        assert config.timeout == 45.0

    def test_env_api_key(self, clean_env: None) -> None:
        os.environ["HARCHOS_API_KEY"] = "hsk_envkey1234567890"
        config = HarchOSConfig()
        assert config.api_key == "hsk_envkey1234567890"

    def test_from_env(self, clean_env: None) -> None:
        os.environ["HARCHOS_API_KEY"] = "hsk_envkey1234567890"
        os.environ["HARCHOS_REGION"] = "france"
        config = HarchOSConfig.from_env()
        assert config.api_key == "hsk_envkey1234567890"
        assert config.region == "france"

    def test_invalid_sovereignty(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            HarchOSConfig(sovereignty="invalid")  # type: ignore[call-arg]

    def test_negative_timeout(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            HarchOSConfig(timeout=-1.0)

    def test_max_retries_out_of_range(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            HarchOSConfig(max_retries=15)


class TestProfile:
    """Tests for the Profile model."""

    def test_default_values(self) -> None:
        profile = Profile(name="test")
        assert profile.name == "test"
        assert profile.base_url == "https://api.harchos.io/v1"
        assert profile.region == "morocco"
        assert profile.sovereignty == "strict"
        assert profile.carbon_aware is True

    def test_region_normalization(self) -> None:
        profile = Profile(name="test", region="Saudi Arabia")
        assert profile.region == "saudi_arabia"

    def test_base_url_strip_slash(self) -> None:
        profile = Profile(name="test", base_url="https://api.test.com/")
        assert profile.base_url == "https://api.test.com"


class TestProfilePersistence:
    """Tests for saving and loading profiles."""

    def test_save_and_load_profile(
        self, tmp_path: pathlib.Path, clean_env: None
    ) -> None:
        # Patch the config directory to use tmp_path
        with (
            patch("harchos.config._CONFIG_DIR", tmp_path),
            patch("harchos.config._PROFILES_FILE", tmp_path / "profiles.json"),
        ):
            config = HarchOSConfig(
                api_key="hsk_testkey1234567890",
                region="uae",
                sovereignty="moderate",
            )
            config.save_as_profile("staging")

            # Load from profile
            loaded = HarchOSConfig.from_profile("staging")
            assert loaded.region == "uae"
            assert loaded.sovereignty == "moderate"

    def test_load_nonexistent_profile(
        self, tmp_path: pathlib.Path, clean_env: None
    ) -> None:
        with (
            patch("harchos.config._CONFIG_DIR", tmp_path),
            patch("harchos.config._PROFILES_FILE", tmp_path / "profiles.json"),
            pytest.raises(KeyError, match="not found"),
        ):
            HarchOSConfig.from_profile("nonexistent")

    def test_save_empty_name_raises(self) -> None:
        config = HarchOSConfig()
        with pytest.raises(ValueError, match="must not be empty"):
            config.save_as_profile("")
