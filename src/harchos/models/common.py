"""Common Pydantic models shared across the HarchOS SDK."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Base model
# ---------------------------------------------------------------------------

class HarchOSBaseModel(BaseModel):
    """Base model with common configuration for all HarchOS models."""

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        from_attributes=True,
        str_strip_whitespace=True,
    )


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

class PaginationMeta(HarchOSBaseModel):
    """Pagination metadata for list responses."""

    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(default=False, description="Whether a next page exists")
    has_prev: bool = Field(default=False, description="Whether a previous page exists")


class PaginatedResponse(HarchOSBaseModel, Generic[T]):
    """Generic paginated response wrapper.

    The ``items`` field holds the actual data for the current page.
    """

    items: List[Any] = Field(default_factory=list, description="Items on this page")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")


# ---------------------------------------------------------------------------
# Common fields
# ---------------------------------------------------------------------------

class ResourceMetadata(HarchOSBaseModel):
    """Standard metadata attached to every HarchOS resource."""

    id: str = Field(..., min_length=1, description="Unique resource identifier")
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp (UTC)")
    labels: Dict[str, str] = Field(default_factory=dict, description="Arbitrary key-value labels")
    annotations: Dict[str, str] = Field(default_factory=dict, description="System annotations")


# ---------------------------------------------------------------------------
# API response envelopes
# ---------------------------------------------------------------------------

class APIResponse(HarchOSBaseModel, Generic[T]):
    """Standard API response envelope."""

    success: bool = Field(..., description="Whether the request succeeded")
    data: Optional[Any] = Field(default=None, description="Response payload")
    message: Optional[str] = Field(default=None, description="Human-readable message")
    request_id: Optional[str] = Field(default=None, description="Unique request tracking ID")


class ErrorResponse(HarchOSBaseModel):
    """Standard error response from the API."""

    success: bool = Field(default=False, description="Always false for errors")
    error: ErrorDetail = Field(..., description="Error details")


class ErrorDetail(HarchOSBaseModel):
    """Detailed error information."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error context")
    field: Optional[str] = Field(default=None, description="Field that caused the error (if applicable)")


# ---------------------------------------------------------------------------
# Health / Status
# ---------------------------------------------------------------------------

class HealthStatus(HarchOSBaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status (healthy, degraded, unhealthy)")
    version: str = Field(default="unknown", description="API version")
    uptime_seconds: Optional[float] = Field(default=None, description="Service uptime in seconds")
    region: Optional[str] = Field(default=None, description="Current region")
