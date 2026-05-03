"""HarchOS SDK HTTP transport layer.

Wraps ``httpx`` with authentication, retry, and sovereign defaults.
Provides both async and sync HTTP clients.
"""

from __future__ import annotations

import json as json_module
from typing import Any, Dict, Optional, Union

import httpx

from ._retry import RetryConfig, retry_async, retry_sync
from .auth import Authenticator
from .config import HarchOSConfig
from .errors import (
    ConnectionError as HarchOSConnectionError,
    HarchOSError,
    TimeoutError as HarchOSTimeoutError,
    raise_for_status,
)

# ---------------------------------------------------------------------------
# User-Agent
# ---------------------------------------------------------------------------

_USER_AGENT = "harchos-sdk-python/0.1.0"
_SDK_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# HTTP transport
# ---------------------------------------------------------------------------

class HttpTransport:
    """Low-level HTTP transport for HarchOS API requests.

    Manages httpx client lifecycle, authentication header injection,
    and automatic retry handling. Supports both async and sync modes.
    """

    def __init__(
        self,
        config: HarchOSConfig,
        auth: Optional[Authenticator] = None,
        *,
        retry_config: Optional[RetryConfig] = None,
    ) -> None:
        self._config = config
        self._auth = auth or Authenticator()
        self._retry_config = retry_config or RetryConfig(
            max_retries=config.max_retries,
        )

        # Build common headers
        self._base_headers: Dict[str, str] = {
            "User-Agent": _USER_AGENT,
            "Accept": "application/json",
            "X-HarchOS-SDK-Version": _SDK_VERSION,
            "X-HarchOS-Region": config.region,
            "X-HarchOS-Sovereignty": config.sovereignty,
        }

        if config.carbon_aware:
            self._base_headers["X-HarchOS-Carbon-Aware"] = "true"

        self._base_headers.update(config.extra_headers)

        # Lazy-init clients
        self._async_client: Optional[httpx.AsyncClient] = None
        self._sync_client: Optional[httpx.Client] = None

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

    # ------------------------------------------------------------------
    # Client lifecycle
    # ------------------------------------------------------------------

    def _build_async_client(self) -> httpx.AsyncClient:
        """Create a new async httpx client."""
        return httpx.AsyncClient(
            base_url=self._config.base_url,
            timeout=httpx.Timeout(self._config.timeout),
            verify=self._config.verify_ssl,
            headers=self._build_headers(),
        )

    def _build_sync_client(self) -> httpx.Client:
        """Create a new sync httpx client."""
        return httpx.Client(
            base_url=self._config.base_url,
            timeout=httpx.Timeout(self._config.timeout),
            verify=self._config.verify_ssl,
            headers=self._build_headers(),
        )

    def _build_headers(self) -> Dict[str, str]:
        """Merge base headers with auth headers."""
        headers = {**self._base_headers}
        auth_headers = self._auth.get_headers()
        headers.update(auth_headers)
        return headers

    async def _get_async_client(self) -> httpx.AsyncClient:
        """Return the async client, creating it if needed."""
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = self._build_async_client()
        return self._async_client

    def _get_sync_client(self) -> httpx.Client:
        """Return the sync client, creating it if needed."""
        if self._sync_client is None or self._sync_client.is_closed:
            self._sync_client = self._build_sync_client()
        return self._sync_client

    # ------------------------------------------------------------------
    # Async request methods
    # ------------------------------------------------------------------

    async def async_request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Execute an async HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.).
            path: URL path (appended to base_url).
            json: JSON body payload.
            params: Query parameters.
            headers: Additional request headers.

        Returns:
            The httpx Response object.

        Raises:
            HarchOSError: On API errors after retries are exhausted.
        """
        client = await self._get_async_client()
        request_headers = self._build_headers()
        if headers:
            request_headers.update(headers)

        async def _do_request() -> httpx.Response:
            try:
                response = await client.request(
                    method=method,
                    url=path,
                    json=json,
                    params=params,
                    headers=request_headers,
                )
            except httpx.TimeoutException as exc:
                raise HarchOSTimeoutError(
                    f"Request to {path} timed out after {self._config.timeout}s"
                ) from exc
            except httpx.ConnectError as exc:
                raise HarchOSConnectionError(
                    f"Failed to connect to {self._config.base_url}{path}"
                ) from exc
            except httpx.HTTPError as exc:
                raise HarchOSConnectionError(
                    f"HTTP error communicating with HarchOS API: {exc}"
                ) from exc

            # Check for errors
            if response.status_code >= 400:
                error_body: Any = None
                error_message = f"HTTP {response.status_code}"
                try:
                    error_body = response.json()
                    if isinstance(error_body, dict):
                        error_message = error_body.get("message", error_body.get("error", error_message))
                except (json_module.JSONDecodeError, ValueError):
                    error_body = response.text

                raise_for_status(
                    status_code=response.status_code,
                    message=str(error_message),
                    headers=dict(response.headers),
                    body=error_body,
                )

            return response

        return await retry_async(_do_request, config=self._retry_config)

    async def async_get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Convenience method for GET requests."""
        return await self.async_request("GET", path, **kwargs)

    async def async_post(self, path: str, **kwargs: Any) -> httpx.Response:
        """Convenience method for POST requests."""
        return await self.async_request("POST", path, **kwargs)

    async def async_put(self, path: str, **kwargs: Any) -> httpx.Response:
        """Convenience method for PUT requests."""
        return await self.async_request("PUT", path, **kwargs)

    async def async_delete(self, path: str, **kwargs: Any) -> httpx.Response:
        """Convenience method for DELETE requests."""
        return await self.async_request("DELETE", path, **kwargs)

    async def async_patch(self, path: str, **kwargs: Any) -> httpx.Response:
        """Convenience method for PATCH requests."""
        return await self.async_request("PATCH", path, **kwargs)

    # ------------------------------------------------------------------
    # Sync request methods
    # ------------------------------------------------------------------

    def sync_request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Execute a synchronous HTTP request with retry logic.

        Args:
            method: HTTP method.
            path: URL path.
            json: JSON body payload.
            params: Query parameters.
            headers: Additional request headers.

        Returns:
            The httpx Response object.

        Raises:
            HarchOSError: On API errors after retries are exhausted.
        """
        client = self._get_sync_client()
        request_headers = self._build_headers()
        if headers:
            request_headers.update(headers)

        def _do_request() -> httpx.Response:
            try:
                response = client.request(
                    method=method,
                    url=path,
                    json=json,
                    params=params,
                    headers=request_headers,
                )
            except httpx.TimeoutException as exc:
                raise HarchOSTimeoutError(
                    f"Request to {path} timed out after {self._config.timeout}s"
                ) from exc
            except httpx.ConnectError as exc:
                raise HarchOSConnectionError(
                    f"Failed to connect to {self._config.base_url}{path}"
                ) from exc
            except httpx.HTTPError as exc:
                raise HarchOSConnectionError(
                    f"HTTP error communicating with HarchOS API: {exc}"
                ) from exc

            if response.status_code >= 400:
                error_body: Any = None
                error_message = f"HTTP {response.status_code}"
                try:
                    error_body = response.json()
                    if isinstance(error_body, dict):
                        error_message = error_body.get("message", error_body.get("error", error_message))
                except (json_module.JSONDecodeError, ValueError):
                    error_body = response.text

                raise_for_status(
                    status_code=response.status_code,
                    message=str(error_message),
                    headers=dict(response.headers),
                    body=error_body,
                )

            return response

        return retry_sync(_do_request, config=self._retry_config)

    def sync_get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Convenience method for sync GET requests."""
        return self.sync_request("GET", path, **kwargs)

    def sync_post(self, path: str, **kwargs: Any) -> httpx.Response:
        """Convenience method for sync POST requests."""
        return self.sync_request("POST", path, **kwargs)

    def sync_put(self, path: str, **kwargs: Any) -> httpx.Response:
        """Convenience method for sync PUT requests."""
        return self.sync_request("PUT", path, **kwargs)

    def sync_delete(self, path: str, **kwargs: Any) -> httpx.Response:
        """Convenience method for sync DELETE requests."""
        return self.sync_request("DELETE", path, **kwargs)

    def sync_patch(self, path: str, **kwargs: Any) -> httpx.Response:
        """Convenience method for sync PATCH requests."""
        return self.sync_request("PATCH", path, **kwargs)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def async_close(self) -> None:
        """Close the async HTTP client."""
        if self._async_client is not None and not self._async_client.is_closed:
            await self._async_client.aclose()
            self._async_client = None

    def sync_close(self) -> None:
        """Close the sync HTTP client."""
        if self._sync_client is not None and not self._sync_client.is_closed:
            self._sync_client.close()
            self._sync_client = None

    async def __aenter__(self) -> "HttpTransport":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.async_close()

    def __enter__(self) -> "HttpTransport":
        return self

    def __exit__(self, *args: Any) -> None:
        self.sync_close()
