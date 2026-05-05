"""HarchOS SDK main client module.

Provides :class:`HarchOSClient` – the primary entry point for interacting
with the HarchOS API. Supports both sync and async usage patterns.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Optional, Type, TypeVar

from ._http import HttpTransport
from ._logging import get_logger
from ._retry import RetryConfig
from ._streaming import async_stream_request
from .auth import Authenticator
from .config import HarchOSConfig
from .models.common import HealthStatus
from .resources.carbon import CarbonResource
from .resources.energy import EnergyResource
from .resources.hubs import HubsResource
from .resources.models import ModelsResource
from .resources.monitoring import MonitoringResource
from .resources.pricing import PricingResource
from .resources.regions import RegionsResource
from .resources.workloads import WorkloadsResource

logger = get_logger("client")

T = TypeVar("T")


class HarchOSClient:
    """The official Python client for the HarchOS API.

    Provides sovereign defaults (``region="morocco"``,
    ``sovereignty="strict"``, ``carbon_aware=True``) and exposes
    resource modules for workloads, models, hubs, and energy.

    Usage (async)::

        async with HarchOSClient(api_key="hsk_...") as client:
            workloads = await client.workloads.async_list()
            for wl in workloads.items:
                print(wl.metadata.name)

    Usage (sync)::

        with HarchOSClient(api_key="hsk_...") as client:
            workloads = client.workloads.list()
            for wl in workloads.items:
                print(wl.metadata.name)

    Args:
        api_key: HarchOS API key (starts with ``hsk_``).
        base_url: API base URL (default: ``https://api.harchos.io/v1``).
        region: Data residency region (default: ``morocco``).
        sovereignty: Sovereignty enforcement level (default: ``strict``).
        carbon_aware: Enable carbon-aware scheduling (default: ``True``).
        timeout: Request timeout in seconds (default: 30).
        max_retries: Maximum retry attempts (default: 3).
        profile: Named configuration profile to load.
        config: A pre-built :class:`HarchOSConfig` instance.
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        region: Optional[str] = None,
        sovereignty: Optional[str] = None,
        carbon_aware: Optional[bool] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        profile: Optional[str] = None,
        config: Optional[HarchOSConfig] = None,
        auth: Optional[Authenticator] = None,
    ) -> None:
        # Build configuration
        config_overrides: Dict[str, Any] = {}
        if api_key is not None:
            config_overrides["api_key"] = api_key
        if base_url is not None:
            config_overrides["base_url"] = base_url
        if region is not None:
            config_overrides["region"] = region
        if sovereignty is not None:
            config_overrides["sovereignty"] = sovereignty
        if carbon_aware is not None:
            config_overrides["carbon_aware"] = carbon_aware
        if timeout is not None:
            config_overrides["timeout"] = timeout
        if max_retries is not None:
            config_overrides["max_retries"] = max_retries
        if profile is not None:
            config_overrides["profile"] = profile

        if config is not None:
            self._config = config
        else:
            self._config = HarchOSConfig(**config_overrides)

        # Build authenticator
        if auth is not None:
            self._auth = auth
        elif self._config.api_key:
            self._auth = Authenticator(api_key=self._config.api_key)
        else:
            self._auth = Authenticator()

        # Build retry config
        self._retry_config = RetryConfig(max_retries=self._config.max_retries)

        # Build HTTP transport
        self._transport = HttpTransport(
            config=self._config,
            auth=self._auth,
            retry_config=self._retry_config,
        )

        # Initialize resource modules
        self._workloads = WorkloadsResource(self._transport)
        self._models = ModelsResource(self._transport)
        self._hubs = HubsResource(self._transport)
        self._energy = EnergyResource(self._transport)
        self._carbon = CarbonResource(self._transport)
        self._pricing = PricingResource(self._transport)
        self._regions = RegionsResource(self._transport)
        self._monitoring = MonitoringResource(self._transport)

        logger.debug(
            "HarchOSClient initialized: base_url=%s region=%s sovereignty=%s",
            self._config.base_url,
            self._config.region,
            self._config.sovereignty,
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def config(self) -> HarchOSConfig:
        """Return the active configuration."""
        return self._config

    @property
    def auth(self) -> Authenticator:
        """Return the authenticator."""
        return self._auth

    @property
    def transport(self) -> HttpTransport:
        """Return the HTTP transport layer."""
        return self._transport

    @property
    def workloads(self) -> WorkloadsResource:
        """Access the workloads resource module."""
        return self._workloads

    @property
    def models(self) -> ModelsResource:
        """Access the models resource module."""
        return self._models

    @property
    def hubs(self) -> HubsResource:
        """Access the hubs resource module."""
        return self._hubs

    @property
    def energy(self) -> EnergyResource:
        """Access the energy resource module."""
        return self._energy

    @property
    def carbon(self) -> CarbonResource:
        """Access the carbon-aware scheduling resource module."""
        return self._carbon

    @property
    def pricing(self) -> PricingResource:
        """Access the pricing and billing resource module."""
        return self._pricing

    @property
    def regions(self) -> RegionsResource:
        """Access the regions resource module."""
        return self._regions

    @property
    def monitoring(self) -> MonitoringResource:
        """Access the monitoring resource module."""
        return self._monitoring

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def async_health(self) -> HealthStatus:
        """Check the health of the HarchOS API (async).

        Returns:
            A :class:`HealthStatus` object.
        """
        response = await self._transport.async_get("/health")
        return HealthStatus.model_validate(response.json())

    def health(self) -> HealthStatus:
        """Check the health of the HarchOS API (sync).

        Returns:
            A :class:`HealthStatus` object.
        """
        response = self._transport.sync_get("/health")
        return HealthStatus.model_validate(response.json())

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------

    async def stream(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        model_class: Optional[Type[T]] = None,
    ) -> AsyncIterator[Any]:
        """Open a streaming request and yield events (async).

        Args:
            method: HTTP method.
            path: URL path.
            json: JSON body payload.
            params: Query parameters.
            model_class: Optional Pydantic model for event validation.

        Yields:
            Parsed streaming events.
        """
        async for item in async_stream_request(
            self._transport,
            method,
            path,
            json=json,
            params=params,
            model_class=model_class,
        ):
            yield item

    # ------------------------------------------------------------------
    # Context managers
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "HarchOSClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def __enter__(self) -> "HarchOSClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close_sync()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the async HTTP client and release resources."""
        await self._transport.async_close()

    def close_sync(self) -> None:
        """Close the sync HTTP client and release resources."""
        self._transport.sync_close()

    def __repr__(self) -> str:
        return (
            f"HarchOSClient("
            f"base_url={self._config.base_url!r}, "
            f"region={self._config.region!r}, "
            f"sovereignty={self._config.sovereignty!r}"
            f")"
        )
