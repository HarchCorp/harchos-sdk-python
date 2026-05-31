"""Tests for the HarchOS client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from harchos import HarchOS, AsyncHarchOS, Config


class TestConfig:
    """Tests for Config initialization."""

    def test_default_init(self) -> None:
        config = Config(api_key="hsk_testapikey1234567890")
        assert config.api_key == "hsk_testapikey1234567890"
        assert config.base_url == "https://api.harchos.ai/v1"
        assert config.timeout == 30.0
        assert config.max_retries == 3

    def test_custom_init(self) -> None:
        config = Config(
            api_key="hsk_testapikey1234567890",
            base_url="https://custom.api.com/v1",
            timeout=60.0,
            max_retries=5,
        )
        assert config.base_url == "https://custom.api.com/v1"
        assert config.timeout == 60.0
        assert config.max_retries == 5

    def test_from_env(self) -> None:
        with patch.dict("os.environ", {"HARCHOS_API_KEY": "hsk_envtestkey1234567890"}):
            config = Config.from_env()
            assert config.api_key == "hsk_envtestkey1234567890"

    def test_repr(self) -> None:
        config = Config(api_key="hsk_testapikey1234567890")
        r = repr(config)
        assert "harchos.ai" in r
        assert "7890" in r


class TestHarchOSClient:
    """Tests for the HarchOS sync client."""

    def test_init(self) -> None:
        client = HarchOS(api_key="hsk_testapikey1234567890")
        assert client is not None

    def test_context_manager(self) -> None:
        with HarchOS(api_key="hsk_testapikey1234567890") as client:
            assert client is not None


class TestAsyncHarchOSClient:
    """Tests for the HarchOS async client."""

    @pytest.mark.asyncio
    async def test_async_init(self) -> None:
        client = AsyncHarchOS(api_key="hsk_testapikey1234567890")
        assert client is not None

    @pytest.mark.asyncio
    async def test_async_context_manager(self) -> None:
        async with AsyncHarchOS(api_key="hsk_testapikey1234567890") as client:
            assert client is not None
