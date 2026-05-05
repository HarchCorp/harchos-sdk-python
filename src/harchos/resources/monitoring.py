"""Monitoring resource module for the HarchOS SDK.

Provides both async and sync methods for platform metrics
and detailed health checks.
"""

from __future__ import annotations

from ..models.monitoring import DetailedHealth, PlatformMetrics
from .base import BaseResource


class MonitoringResource(BaseResource):
    """Manages platform monitoring and health data.

    Use this resource to:

    * Get aggregate platform metrics (GPUs, workloads, energy, carbon)
    * Perform detailed health checks

    Usage::

        client = HarchOSClient(api_key="hsk_...")

        # Get platform metrics
        metrics = client.monitoring.metrics()
        print(f"Total GPUs: {metrics.total_gpus}, Utilization: {metrics.gpu_utilization_percent}%")

        # Detailed health check
        health = client.monitoring.detailed_health()
        print(f"Status: {health.status}, DB: {health.database_status}, Uptime: {health.uptime_hours}h")
    """

    _resource_path = "/monitoring"

    # ------------------------------------------------------------------
    # Async methods
    # ------------------------------------------------------------------

    async def async_metrics(self) -> PlatformMetrics:
        """Get aggregate platform metrics (async).

        Returns:
            A :class:`PlatformMetrics` object with platform-wide stats.
        """
        response = await self._transport.async_get("/monitoring/metrics")
        return PlatformMetrics.model_validate(response.json())

    async def async_detailed_health(self) -> DetailedHealth:
        """Get a detailed health check of the platform (async).

        Returns:
            A :class:`DetailedHealth` object with server and DB status.
        """
        response = await self._transport.async_get("/monitoring/health/detailed")
        return DetailedHealth.model_validate(response.json())

    # ------------------------------------------------------------------
    # Sync methods
    # ------------------------------------------------------------------

    def metrics(self) -> PlatformMetrics:
        """Get aggregate platform metrics (sync).

        Returns:
            A :class:`PlatformMetrics` object with platform-wide stats.
        """
        response = self._transport.sync_get("/monitoring/metrics")
        return PlatformMetrics.model_validate(response.json())

    def detailed_health(self) -> DetailedHealth:
        """Get a detailed health check of the platform (sync).

        Returns:
            A :class:`DetailedHealth` object with server and DB status.
        """
        response = self._transport.sync_get("/monitoring/health/detailed")
        return DetailedHealth.model_validate(response.json())
