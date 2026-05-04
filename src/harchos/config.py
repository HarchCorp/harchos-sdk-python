"""HarchOS SDK configuration management.

Provides :class:`HarchOSConfig` with sovereign defaults and profile-based
configuration. Supports environment variables, programmatic overrides, and
persistent profiles stored as JSON.
"""

from __future__ import annotations

import contextlib
import json
import os
import pathlib
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_BASE_URL = "https://api.harchos.io/v1"
_DEFAULT_REGION = "morocco"
_DEFAULT_SOVEREIGNTY = "strict"
_DEFAULT_TIMEOUT = 30.0
_DEFAULT_MAX_RETRIES = 3
_CONFIG_DIR = pathlib.Path.home() / ".harchos"
_PROFILES_FILE = _CONFIG_DIR / "profiles.json"

SovereigntyLevel = Literal["strict", "moderate", "minimal"]
Region = Literal[
    "morocco",
    "algeria",
    "tunisia",
    "uae",
    "saudi_arabia",
    "france",
    "germany",
    "eu_west",
    "us_east",
    "us_west",
    "asia_east",
]


# ---------------------------------------------------------------------------
# Profile model
# ---------------------------------------------------------------------------

class Profile(BaseModel):
    """A named configuration profile.

    Profiles allow switching between different HarchOS environments
    (e.g. production vs. staging) without changing code.
    """

    name: str = Field(..., min_length=1, description="Unique profile name")
    base_url: str = Field(default=_DEFAULT_BASE_URL, description="API base URL")
    region: str = Field(default=_DEFAULT_REGION, description="Data residency region")
    sovereignty: SovereigntyLevel = Field(  # type: ignore[assignment]
        default=_DEFAULT_SOVEREIGNTY,
        description="Sovereignty enforcement level",
    )
    api_key: Optional[str] = Field(default=None, description="API key for this profile")
    timeout: float = Field(default=_DEFAULT_TIMEOUT, gt=0, description="Request timeout in seconds")
    max_retries: int = Field(
        default=_DEFAULT_MAX_RETRIES, ge=0, le=10, description="Maximum retry attempts"
    )
    carbon_aware: bool = Field(default=True, description="Enable carbon-aware scheduling")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")

    @field_validator("region", mode="before")
    @classmethod
    def normalize_region(cls, v: str) -> str:
        """Normalize region strings to lowercase with underscores."""
        return v.lower().replace("-", "_").replace(" ", "_")

    @field_validator("base_url", mode="after")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        """Remove trailing slash from base URL to avoid double slashes."""
        return v.rstrip("/")


# ---------------------------------------------------------------------------
# Main configuration
# ---------------------------------------------------------------------------

class HarchOSConfig(BaseModel):
    """Main SDK configuration with sovereign defaults.

    The configuration can be built from:
    - Direct keyword arguments (highest priority)
    - A named profile loaded from ``~/.harchos/profiles.json``
    - Environment variables prefixed with ``HARCHOS_``
    - Built-in sovereign defaults (lowest priority)

    Example::

        config = HarchOSConfig(
            api_key="hsk_...",
            region="morocco",
            sovereignty="strict",
            carbon_aware=True,
        )
    """

    base_url: str = Field(default=_DEFAULT_BASE_URL, description="API base URL")
    region: str = Field(default=_DEFAULT_REGION, description="Data residency region")
    sovereignty: SovereigntyLevel = Field(  # type: ignore[assignment]
        default=_DEFAULT_SOVEREIGNTY,
        description="Sovereignty enforcement level",
    )
    api_key: Optional[str] = Field(default=None, description="API key")
    timeout: float = Field(default=_DEFAULT_TIMEOUT, gt=0, description="Request timeout in seconds")
    max_retries: int = Field(
        default=_DEFAULT_MAX_RETRIES, ge=0, le=10, description="Maximum retry attempts"
    )
    carbon_aware: bool = Field(default=True, description="Enable carbon-aware scheduling")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    profile: Optional[str] = Field(default=None, description="Named profile to load")

    # Internal – not serialized
    extra_headers: Dict[str, str] = Field(
        default_factory=dict, description="Extra HTTP headers to send with every request"
    )

    model_config = {"extra": "ignore"}

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("region", mode="before")
    @classmethod
    def normalize_region(cls, v: str) -> str:
        """Normalize region strings to lowercase with underscores."""
        return v.lower().replace("-", "_").replace(" ", "_")

    @field_validator("base_url", mode="after")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        """Remove trailing slash from base URL."""
        return v.rstrip("/")

    @field_validator("api_key", mode="before")
    @classmethod
    def strip_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Strip whitespace from API key."""
        if v is not None:
            return v.strip()
        return v

    @model_validator(mode="after")
    def _apply_profile_and_env(self) -> "HarchOSConfig":
        """Overlay profile and environment variable values where not explicitly set.

        Priority order (highest to lowest):
        1. Constructor arguments (explicitly set fields)
        2. Environment variables (HARCHOS_*)
        3. Profile values
        4. Built-in defaults
        """
        # Load profile if specified
        if self.profile and self.profile != "default":
            profile_data = _load_profile(self.profile)
            if profile_data:
                for key, value in profile_data.items():
                    if key == "name":
                        continue
                    if not hasattr(self, key):
                        continue
                    # Only override if the field is still at its default
                    field_info = HarchOSConfig.model_fields.get(key)
                    if field_info is not None and key not in self.model_fields_set:
                        current = getattr(self, key)
                        if current == field_info.default and value is not None:
                            object.__setattr__(self, key, value)

        # Apply environment variables ONLY for fields not explicitly set by constructor
        env_mapping: Dict[str, tuple[str, type]] = {
            "HARCHOS_API_KEY": ("api_key", str),
            "HARCHOS_BASE_URL": ("base_url", str),
            "HARCHOS_REGION": ("region", str),
            "HARCHOS_SOVEREIGNTY": ("sovereignty", str),
            "HARCHOS_TIMEOUT": ("timeout", float),
            "HARCHOS_MAX_RETRIES": ("max_retries", int),
        }

        for env_var, (field_name, field_type) in env_mapping.items():
            if field_name not in self.model_fields_set:  # Only override if not explicitly set
                env_val = os.environ.get(env_var)
                if env_val is not None:
                    if field_type is int:
                        with contextlib.suppress(ValueError):
                            setattr(self, field_name, int(env_val))
                    elif field_type is float:
                        with contextlib.suppress(ValueError):
                            setattr(self, field_name, float(env_val))
                    else:
                        setattr(self, field_name, env_val)

        return self

    # ------------------------------------------------------------------
    # Profile management
    # ------------------------------------------------------------------

    def save_as_profile(self, name: str) -> None:
        """Persist the current configuration as a named profile.

        Args:
            name: Profile name (must be non-empty).

        Raises:
            ValueError: If *name* is empty.
        """
        if not name.strip():
            raise ValueError("Profile name must not be empty")

        profiles = _load_all_profiles()
        profile = Profile(
            name=name,
            base_url=self.base_url,
            region=self.region,
            sovereignty=self.sovereignty,
            api_key=self.api_key,
            timeout=self.timeout,
            max_retries=self.max_retries,
            carbon_aware=self.carbon_aware,
            verify_ssl=self.verify_ssl,
        )
        profiles[name] = profile.model_dump(mode="json")
        _save_profiles(profiles)

    @classmethod
    def from_profile(cls, name: str, **overrides: Any) -> "HarchOSConfig":
        """Create a configuration from a named profile with optional overrides.

        Args:
            name: The profile name to load.
            **overrides: Keyword overrides applied on top of the profile.

        Returns:
            A new :class:`HarchOSConfig` instance.

        Raises:
            FileNotFoundError: If the profiles file does not exist.
            KeyError: If the profile *name* is not found.
        """
        profile_data = _load_profile(name)
        if profile_data is None:
            raise KeyError(f"Profile '{name}' not found")
        profile_data.pop("name", None)
        profile_data.update(overrides)
        return cls(**profile_data)

    @classmethod
    def from_env(cls, **overrides: Any) -> "HarchOSConfig":
        """Create a configuration primarily from environment variables.

        Environment variables:

        - ``HARCHOS_API_KEY``
        - ``HARCHOS_BASE_URL``
        - ``HARCHOS_REGION``
        - ``HARCHOS_TIMEOUT``
        - ``HARCHOS_MAX_RETRIES``
        - ``HARCHOS_SOVEREIGNTY``

        Args:
            **overrides: Keyword overrides with highest priority.

        Returns:
            A new :class:`HarchOSConfig` instance.
        """
        return cls(**overrides)


# ---------------------------------------------------------------------------
# Profile persistence helpers
# ---------------------------------------------------------------------------

def _load_all_profiles() -> Dict[str, Dict[str, Any]]:
    """Load all profiles from the profiles file."""
    if not _PROFILES_FILE.exists():
        return {}
    try:
        data = json.loads(_PROFILES_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _load_profile(name: str) -> Optional[Dict[str, Any]]:
    """Load a single profile by name."""
    profiles = _load_all_profiles()
    return profiles.get(name)


def _save_profiles(profiles: Dict[str, Dict[str, Any]]) -> None:
    """Persist all profiles to the profiles file."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _PROFILES_FILE.write_text(
        json.dumps(profiles, indent=2, sort_keys=True),
        encoding="utf-8",
    )
