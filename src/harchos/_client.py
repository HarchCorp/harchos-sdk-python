"""HarchOS SDK client module.

Provides :class:`HarchOS` (sync) and :class:`AsyncHarchOS` (async) clients
as the primary entry points for interacting with the HarchOS API.

Usage (sync)::

    from harchos import HarchOS

    client = HarchOS(api_key="hsk_...")
    response = client.inference.chat.completions.create(
        model="harchos-llama-3.3-70b",
        messages=[{"role": "user", "content": "Hello"}],
    )
    print(response.choices[0].message.content)

Usage (async)::

    from harchos import AsyncHarchOS

    async with AsyncHarchOS(api_key="hsk_...") as client:
        response = await client.inference.chat.completions.create(
            model="harchos-llama-3.3-70b",
            messages=[{"role": "user", "content": "Hello"}],
        )
"""

from __future__ import annotations

import json as json_module
from typing import Any, Dict, Optional

import httpx

from ._config import Config
from ._exceptions import HarchOSError, make_error
from ._retry import RetryConfig, retry_async, retry_sync
from .resources.auth import AuthResource, AsyncAuthResource
from .resources.carbon import CarbonResource, AsyncCarbonResource
from .resources.hubs import HubsResource, AsyncHubsResource
from .resources.inference import InferenceResource, AsyncInferenceResource
from .resources.pricing import PricingResource, AsyncPricingResource
from .resources.workloads import WorkloadsResource, AsyncWorkloadsResource

# SDK version
__version__ = "0.3.0"

_USER_AGENT = f"harchos-sdk-python/{__version__}"


class _BaseClient:
    """Shared initialization logic for sync and async clients."""

    def _init(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: int = 3,
        default_headers: Optional[Dict[str, str]] = None,
        config: Optional[Config] = None,
    ) -> None:
        if config is not None:
            self._config = config
        else:
            config_kwargs: Dict[str, Any] = {
                "api_key": api_key,
                "timeout": timeout or 30.0,
                "max_retries": max_retries,
                "default_headers": default_headers,
            }
            if base_url is not None:
                config_kwargs["base_url"] = base_url
            self._config = Config(**config_kwargs)

        self._retry_config = RetryConfig(max_retries=self._config.max_retries)
        self._base_headers: Dict[str, str] = {
            "User-Agent": _USER_AGENT,
            "Accept": "application/json",
            "X-HarchOS-SDK-Version": __version__,
        }
        if self._config.api_key:
            self._base_headers["Authorization"] = f"Bearer {self._config.api_key}"
        self._base_headers.update(self._config.default_headers)

        # Lazy-init clients
        self._async_client: Optional[httpx.AsyncClient] = None
        self._sync_client: Optional[httpx.Client] = None

    def _build_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Merge base headers with extra headers."""
        headers = {**self._base_headers}
        if extra:
            headers.update(extra)
        return headers

    def _handle_response(self, response: httpx.Response) -> Any:
        """Process an HTTP response, raising on errors.

        Returns the parsed JSON body on success.
        """
        if 200 <= response.status_code < 300:
            try:
                return response.json()
            except (json_module.JSONDecodeError, ValueError):
                return response.text

        # Error path
        try:
            body = response.json()
        except (json_module.JSONDecodeError, ValueError):
            body = response.text

        raise make_error(
            status_code=response.status_code,
            message=f"HTTP {response.status_code}",
            body=body,
            headers=dict(response.headers),
        )


class HarchOS(_BaseClient):
    """The official synchronous Python client for the HarchOS API.

    Provides sovereign AI infrastructure access with built-in carbon tracking,
    OpenAI-compatible inference, and carbon-aware workload scheduling.

    Args:
        api_key: HarchOS API key (starts with ``hsk_``).
        base_url: API base URL. Defaults to ``https://api.harchos.ai/v1``.
        timeout: Request timeout in seconds.
        max_retries: Maximum retry attempts (default: 3).
        default_headers: Extra HTTP headers for every request.
        config: Pre-built :class:`Config` instance.

    Example::

        from harchos import HarchOS

        client = HarchOS(api_key="hsk_...")
        response = client.inference.chat.completions.create(
            model="harchos-llama-3.3-70b",
            messages=[{"role": "user", "content": "Hello"}],
        )
        print(response.content)
        print(f"Carbon: {response.carbon_footprint.gco2}g CO2")
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: int = 3,
        default_headers: Optional[Dict[str, str]] = None,
        config: Optional[Config] = None,
    ) -> None:
        self._init(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
            config=config,
        )
        # Initialize resource modules
        self._inference = InferenceResource(self)
        self._workloads = WorkloadsResource(self)
        self._hubs = HubsResource(self)
        self._carbon = CarbonResource(self)
        self._pricing = PricingResource(self)
        self._auth = AuthResource(self)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def inference(self) -> InferenceResource:
        """Access the inference resource module."""
        return self._inference

    @property
    def workloads(self) -> WorkloadsResource:
        """Access the workloads resource module."""
        return self._workloads

    @property
    def hubs(self) -> HubsResource:
        """Access the hubs resource module."""
        return self._hubs

    @property
    def carbon(self) -> CarbonResource:
        """Access the carbon resource module."""
        return self._carbon

    @property
    def pricing(self) -> PricingResource:
        """Access the pricing resource module."""
        return self._pricing

    @property
    def auth(self) -> AuthResource:
        """Access the auth resource module."""
        return self._auth

    @property
    def config(self) -> Config:
        """Return the active configuration."""
        return self._config

    # ------------------------------------------------------------------
    # HTTP methods (sync)
    # ------------------------------------------------------------------

    def _get_sync_client(self) -> httpx.Client:
        if self._sync_client is None or self._sync_client.is_closed:
            self._sync_client = httpx.Client(
                base_url=self._config.base_url,
                timeout=httpx.Timeout(self._config.timeout),
                headers=self._base_headers,
            )
        return self._sync_client

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        stream: bool = False,
    ) -> Any:
        """Execute a synchronous HTTP request with retry logic.

        Returns:
            Parsed JSON response body on success.

        Raises:
            HarchOSError: On API errors after retries are exhausted.
        """
        client = self._get_sync_client()
        request_headers = self._build_headers(headers)

        def _do() -> httpx.Response:
            return client.request(
                method=method,
                url=path,
                json=json,
                params=params,
                headers=request_headers,
            )

        response = retry_sync(_do, config=self._retry_config)
        return self._handle_response(response)

    def stream_request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Open a sync streaming request. Caller must close the response."""
        client = self._get_sync_client()
        request_headers = self._build_headers(headers)
        request_headers["Accept"] = "text/event-stream"

        request = client.build_request(
            method=method,
            url=path,
            json=json,
            params=params,
            headers=request_headers,
        )
        return client.send(request, stream=True)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "HarchOS":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the sync HTTP client and release resources."""
        if self._sync_client is not None and not self._sync_client.is_closed:
            self._sync_client.close()
            self._sync_client = None

    def __repr__(self) -> str:
        return f"HarchOS(base_url={self._config.base_url!r})"


class AsyncHarchOS(_BaseClient):
    """The official asynchronous Python client for the HarchOS API.

    All methods are async and return coroutines. Use as an async context
    manager for proper resource cleanup.

    Args:
        api_key: HarchOS API key (starts with ``hsk_``).
        base_url: API base URL. Defaults to ``https://api.harchos.ai/v1``.
        timeout: Request timeout in seconds.
        max_retries: Maximum retry attempts (default: 3).
        default_headers: Extra HTTP headers for every request.
        config: Pre-built :class:`Config` instance.

    Example::

        from harchos import AsyncHarchOS

        async with AsyncHarchOS(api_key="hsk_...") as client:
            response = await client.inference.chat.completions.create(
                model="harchos-llama-3.3-70b",
                messages=[{"role": "user", "content": "Hello"}],
            )
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: int = 3,
        default_headers: Optional[Dict[str, str]] = None,
        config: Optional[Config] = None,
    ) -> None:
        self._init(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
            config=config,
        )
        # Initialize async resource modules
        self._inference = AsyncInferenceResource(self)
        self._workloads = AsyncWorkloadsResource(self)
        self._hubs = AsyncHubsResource(self)
        self._carbon = AsyncCarbonResource(self)
        self._pricing = AsyncPricingResource(self)
        self._auth = AsyncAuthResource(self)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def inference(self) -> AsyncInferenceResource:
        """Access the async inference resource module."""
        return self._inference

    @property
    def workloads(self) -> AsyncWorkloadsResource:
        """Access the async workloads resource module."""
        return self._workloads

    @property
    def hubs(self) -> AsyncHubsResource:
        """Access the async hubs resource module."""
        return self._hubs

    @property
    def carbon(self) -> AsyncCarbonResource:
        """Access the async carbon resource module."""
        return self._carbon

    @property
    def pricing(self) -> AsyncPricingResource:
        """Access the async pricing resource module."""
        return self._pricing

    @property
    def auth(self) -> AsyncAuthResource:
        """Access the async auth resource module."""
        return self._auth

    @property
    def config(self) -> Config:
        """Return the active configuration."""
        return self._config

    # ------------------------------------------------------------------
    # HTTP methods (async)
    # ------------------------------------------------------------------

    async def _get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(
                base_url=self._config.base_url,
                timeout=httpx.Timeout(self._config.timeout),
                headers=self._base_headers,
            )
        return self._async_client

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Execute an async HTTP request with retry logic.

        Returns:
            Parsed JSON response body on success.

        Raises:
            HarchOSError: On API errors after retries are exhausted.
        """
        client = await self._get_async_client()
        request_headers = self._build_headers(headers)

        async def _do() -> httpx.Response:
            return await client.request(
                method=method,
                url=path,
                json=json,
                params=params,
                headers=request_headers,
            )

        response = await retry_async(_do, config=self._retry_config)
        return self._handle_response(response)

    async def stream_request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Open an async streaming request. Caller must close the response."""
        client = await self._get_async_client()
        request_headers = self._build_headers(headers)
        request_headers["Accept"] = "text/event-stream"

        request = client.build_request(
            method=method,
            url=path,
            json=json,
            params=params,
            headers=request_headers,
        )
        return await client.send(request, stream=True)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "AsyncHarchOS":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the async HTTP client and release resources."""
        if self._async_client is not None and not self._async_client.is_closed:
            await self._async_client.aclose()
            self._async_client = None

    def __repr__(self) -> str:
        return f"AsyncHarchOS(base_url={self._config.base_url!r})"
