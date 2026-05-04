"""Tests for energy resource module."""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from harchos import HarchOSClient
from harchos.models.energy import EnergyConsumption, EnergyReport, EnergySummary, GreenWindow


class TestEnergyAsync:
    """Tests for async energy operations."""

    @pytest.mark.asyncio
    async def test_async_get_report(self, sample_energy_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = sample_energy_data
        with patch.object(
            client._transport, "async_get", new_callable=AsyncMock, return_value=mock_response
        ):
            report = await client.energy.async_get_report("wl_abc123")
            assert isinstance(report, EnergyReport)
            assert report.resource_id == "wl_abc123"

    @pytest.mark.asyncio
    async def test_async_get_summary(self) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        summary_data = {
            "total_kwh": 500.0,
            "total_co2_grams": 150.0,
            "average_pue": 1.2,
            "average_renewable_fraction": 0.65,
            "resource_count": 10,
            "period_start": "2024-01-01T00:00:00Z",
            "period_end": "2024-01-31T23:59:59Z",
        }
        mock_response = MagicMock()
        mock_response.json.return_value = summary_data
        with patch.object(
            client._transport, "async_get", new_callable=AsyncMock, return_value=mock_response
        ):
            summary = await client.energy.async_get_summary(region="morocco")
            assert isinstance(summary, EnergySummary)
            assert summary.total_kwh == 500.0

    @pytest.mark.asyncio
    async def test_async_get_green_windows(self) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        windows_data = {
            "items": [
                {
                    "start": "2024-01-15T10:00:00Z",
                    "end": "2024-01-15T14:00:00Z",
                    "renewable_percentage": 85.0,
                    "estimated_co2_grams_per_kwh": 50.0,
                }
            ]
        }
        mock_response = MagicMock()
        mock_response.json.return_value = windows_data
        with patch.object(
            client._transport, "async_get", new_callable=AsyncMock, return_value=mock_response
        ):
            windows = await client.energy.async_get_green_windows(region="morocco")
            assert len(windows) == 1
            assert isinstance(windows[0], GreenWindow)

    @pytest.mark.asyncio
    async def test_async_get_consumption(self) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        consumption_data = {
            "kwh_consumed": 150.5,
            "co2_grams": 45.2,
            "pue": 1.15,
            "renewable_fraction": 0.65,
            "grid_intensity_gco2_kwh": 300.0,
            "period_start": "2024-01-15T10:00:00Z",
            "period_end": "2024-01-15T11:00:00Z",
        }
        mock_response = MagicMock()
        mock_response.json.return_value = consumption_data
        with patch.object(
            client._transport, "async_get", new_callable=AsyncMock, return_value=mock_response
        ):
            ec = await client.energy.async_get_consumption("wl_abc123")
            assert isinstance(ec, EnergyConsumption)
            assert ec.kwh_consumed == 150.5


class TestEnergySync:
    """Tests for sync energy operations."""

    def test_get_report(self, sample_energy_data: Dict[str, Any]) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        mock_response = MagicMock()
        mock_response.json.return_value = sample_energy_data
        with patch.object(client._transport, "sync_get", return_value=mock_response):
            report = client.energy.get_report("wl_abc123")
            assert isinstance(report, EnergyReport)

    def test_get_summary(self) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        summary_data = {
            "total_kwh": 500.0,
            "total_co2_grams": 150.0,
            "average_pue": 1.2,
            "average_renewable_fraction": 0.65,
            "resource_count": 10,
            "period_start": "2024-01-01T00:00:00Z",
            "period_end": "2024-01-31T23:59:59Z",
        }
        mock_response = MagicMock()
        mock_response.json.return_value = summary_data
        with patch.object(client._transport, "sync_get", return_value=mock_response):
            summary = client.energy.get_summary()
            assert isinstance(summary, EnergySummary)

    def test_get_green_windows_list_format(self) -> None:
        client = HarchOSClient(api_key="hsk_testapikey1234567890")
        windows_data = [
            {
                "start": "2024-01-15T10:00:00Z",
                "end": "2024-01-15T14:00:00Z",
                "renewable_percentage": 85.0,
                "estimated_co2_grams_per_kwh": 50.0,
            }
        ]
        mock_response = MagicMock()
        mock_response.json.return_value = windows_data
        with patch.object(client._transport, "sync_get", return_value=mock_response):
            windows = client.energy.get_green_windows(region="morocco")
            assert len(windows) == 1
            assert isinstance(windows[0], GreenWindow)
