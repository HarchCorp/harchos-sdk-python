"""Tests for model resource module."""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from harchos import HarchOSClient
from harchos.models.model import (
    Model,
    ModelFramework,
    ModelList,
    ModelSpec,
    ModelStatus,
    ModelTask,
)


class TestModelsAsync:
    """Tests for async model operations."""

    @pytest.mark.asyncio
    async def test_async_list(self, sample_model_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [sample_model_data],
            "total": 1,
        }
        with patch.object(
            client._transport, "async_get", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await client.models.async_list()
            assert isinstance(result, ModelList)
            assert result.total == 1

    @pytest.mark.asyncio
    async def test_async_get(self, sample_model_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = sample_model_data
        with patch.object(
            client._transport, "async_get", new_callable=AsyncMock, return_value=mock_response
        ):
            model = await client.models.async_get("mdl_def456")
            assert model.metadata.id == "mdl_def456"

    @pytest.mark.asyncio
    async def test_async_create(self, sample_model_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = sample_model_data
        with patch.object(
            client._transport, "async_post", new_callable=AsyncMock, return_value=mock_response
        ):
            spec = ModelSpec(
                name="test-model",
                framework=ModelFramework.PYTORCH,
                task=ModelTask.TEXT_GENERATION,
            )
            model = await client.models.async_create(spec)
            assert isinstance(model, Model)

    @pytest.mark.asyncio
    async def test_async_deploy(self, sample_model_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        deployed_data = {**sample_model_data, "status": "deploying"}
        mock_response = MagicMock()
        mock_response.json.return_value = deployed_data
        with patch.object(
            client._transport, "async_patch", new_callable=AsyncMock, return_value=mock_response
        ):
            model = await client.models.async_deploy("mdl_def456")
            assert model.status == ModelStatus.DEPLOYING


class TestModelsSync:
    """Tests for sync model operations."""

    def test_list(self, sample_model_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [sample_model_data],
            "total": 1,
        }
        with patch.object(client._transport, "sync_get", return_value=mock_response):
            result = client.models.list()
            assert isinstance(result, ModelList)

    def test_get(self, sample_model_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = sample_model_data
        with patch.object(client._transport, "sync_get", return_value=mock_response):
            model = client.models.get("mdl_def456")
            assert model.metadata.id == "mdl_def456"

    def test_deploy(self, sample_model_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        deployed_data = {**sample_model_data, "status": "deploying"}
        mock_response = MagicMock()
        mock_response.json.return_value = deployed_data
        with patch.object(client._transport, "sync_patch", return_value=mock_response):
            model = client.models.deploy("mdl_def456")
            assert model.status == ModelStatus.DEPLOYING
