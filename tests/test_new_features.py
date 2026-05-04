"""Tests for new features added in the bug-fix sprint.

Covers:
- ResourceMetadata.name field
- Config env var priority (constructor > env > profile)
- Pandas to_dataframe() (with mock)
- Logging configuration
"""

from __future__ import annotations

import logging
import os
from unittest.mock import MagicMock, patch

import pytest

from harchos._logging import configure_logging, get_logger
from harchos.config import HarchOSConfig
from harchos.models.common import PaginatedResponse, PaginationMeta, ResourceMetadata
from harchos.models.hub import Hub, HubList
from harchos.models.model import Model, ModelList
from harchos.models.workload import Workload, WorkloadList


# ---------------------------------------------------------------------------
# ResourceMetadata.name
# ---------------------------------------------------------------------------


class TestResourceMetadataName:
    """Tests for the new name field on ResourceMetadata."""

    def test_name_field_defaults_to_none(self) -> None:
        meta = ResourceMetadata(
            id="wl_abc123",
            created_at="2024-01-15T10:30:00Z",
        )
        assert meta.name is None

    def test_name_field_can_be_set(self) -> None:
        meta = ResourceMetadata(
            id="wl_abc123",
            name="my-workload",
            created_at="2024-01-15T10:30:00Z",
        )
        assert meta.name == "my-workload"

    def test_metadata_name_access_pattern(self) -> None:
        """Verify wl.metadata.name works as documented in README."""
        meta = ResourceMetadata(
            id="wl_abc123",
            name="gpt4-training",
            created_at="2024-01-15T10:30:00Z",
        )
        assert meta.name == "gpt4-training"

    def test_metadata_name_and_spec_name_can_differ(self) -> None:
        """metadata.name is display name, spec.name is identifier — they can differ."""
        from harchos.models.workload import WorkloadSpec, WorkloadType

        meta = ResourceMetadata(
            id="wl_abc123",
            name="My Training Job (display)",
            created_at="2024-01-15T10:30:00Z",
        )
        spec = WorkloadSpec(name="my-training-job-identifier", type=WorkloadType.TRAINING)
        wl = Workload(metadata=meta, spec=spec)
        # metadata.name is the display name
        assert wl.metadata.name == "My Training Job (display)"
        # spec.name is the identifier
        assert wl.spec.name == "my-training-job-identifier"


# ---------------------------------------------------------------------------
# Config env var priority
# ---------------------------------------------------------------------------


class TestConfigEnvVarPriority:
    """Tests for constructor args > env vars > profile > defaults."""

    def test_constructor_overrides_env(self, clean_env: None) -> None:
        """Constructor args should take priority over env vars."""
        os.environ["HARCHOS_REGION"] = "germany"
        config = HarchOSConfig(region="uae")
        # Constructor "uae" should win over env var "germany"
        assert config.region == "uae"

    def test_env_overrides_defaults(self, clean_env: None) -> None:
        """Env vars should override defaults when no constructor arg is given."""
        os.environ["HARCHOS_REGION"] = "germany"
        config = HarchOSConfig()
        assert config.region == "germany"

    def test_constructor_api_key_overrides_env(self, clean_env: None) -> None:
        os.environ["HARCHOS_API_KEY"] = "hsk_envkey1234567890"
        config = HarchOSConfig(api_key="hsk_ctrkey1234567890XXX")
        assert config.api_key == "hsk_ctrkey1234567890XXX"

    def test_constructor_timeout_overrides_env(self, clean_env: None) -> None:
        os.environ["HARCHOS_TIMEOUT"] = "99.0"
        config = HarchOSConfig(timeout=42.0)
        assert config.timeout == 42.0

    def test_env_timeout_when_not_explicit(self, clean_env: None) -> None:
        os.environ["HARCHOS_TIMEOUT"] = "45.0"
        config = HarchOSConfig()
        assert config.timeout == 45.0

    def test_constructor_max_retries_overrides_env(self, clean_env: None) -> None:
        os.environ["HARCHOS_MAX_RETRIES"] = "8"
        config = HarchOSConfig(max_retries=2)
        assert config.max_retries == 2

    def test_env_max_retries_when_not_explicit(self, clean_env: None) -> None:
        os.environ["HARCHOS_MAX_RETRIES"] = "7"
        config = HarchOSConfig()
        assert config.max_retries == 7

    def test_constructor_sovereignty_overrides_env(self, clean_env: None) -> None:
        os.environ["HARCHOS_SOVEREIGNTY"] = "minimal"
        config = HarchOSConfig(sovereignty="strict")
        assert config.sovereignty == "strict"

    def test_env_sovereignty_when_not_explicit(self, clean_env: None) -> None:
        os.environ["HARCHOS_SOVEREIGNTY"] = "moderate"
        config = HarchOSConfig()
        assert config.sovereignty == "moderate"

    def test_no_env_no_constructor_uses_defaults(self, clean_env: None) -> None:
        config = HarchOSConfig()
        assert config.region == "morocco"
        assert config.sovereignty == "strict"
        assert config.timeout == 30.0
        assert config.max_retries == 3


# ---------------------------------------------------------------------------
# Pandas to_dataframe() (with mock)
# ---------------------------------------------------------------------------


class TestToDataframe:
    """Tests for to_dataframe() method on list models."""

    def test_to_dataframe_without_pandas_raises(self) -> None:
        """to_dataframe() should raise ImportError when pandas is not installed."""
        wl_list = WorkloadList(items=[], total=0)
        with patch.dict("sys.modules", {"pandas": None}):
            with pytest.raises(ImportError, match="pandas is required"):
                wl_list.to_dataframe()

    def test_to_dataframe_with_mock_pandas(self) -> None:
        """to_dataframe() should call pd.DataFrame when pandas is available."""
        mock_pd = MagicMock()
        mock_df = MagicMock()
        mock_pd.DataFrame.return_value = mock_df

        wl_list = WorkloadList(items=[], total=0)
        with patch.dict("sys.modules", {"pandas": mock_pd}):
            result = wl_list.to_dataframe()
            assert result is mock_df
            mock_pd.DataFrame.assert_called_once()

    def test_model_list_to_dataframe_with_mock_pandas(self) -> None:
        mock_pd = MagicMock()
        mock_df = MagicMock()
        mock_pd.DataFrame.return_value = mock_df

        model_list = ModelList(items=[], total=0)
        with patch.dict("sys.modules", {"pandas": mock_pd}):
            result = model_list.to_dataframe()
            assert result is mock_df

    def test_hub_list_to_dataframe_with_mock_pandas(self) -> None:
        mock_pd = MagicMock()
        mock_df = MagicMock()
        mock_pd.DataFrame.return_value = mock_df

        hub_list = HubList(items=[], total=0)
        with patch.dict("sys.modules", {"pandas": mock_pd}):
            result = hub_list.to_dataframe()
            assert result is mock_df

    def test_paginated_response_to_dataframe_with_mock_pandas(self) -> None:
        mock_pd = MagicMock()
        mock_df = MagicMock()
        mock_pd.DataFrame.return_value = mock_df

        pag = PaginatedResponse(
            items=[],
            pagination=PaginationMeta(total=0, page=1, per_page=10, total_pages=0),
        )
        with patch.dict("sys.modules", {"pandas": mock_pd}):
            result = pag.to_dataframe()
            assert result is mock_df


# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------


class TestLogging:
    """Tests for the _logging module."""

    def test_get_logger_returns_logger(self) -> None:
        log = get_logger()
        assert isinstance(log, logging.Logger)
        assert log.name == "harchos"

    def test_get_logger_with_child_name(self) -> None:
        log = get_logger("http")
        assert log.name == "harchos.http"

    def test_configure_logging_sets_level(self) -> None:
        # Remove existing handlers to avoid pollution
        root_logger = logging.getLogger("harchos")
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        configure_logging(level=logging.DEBUG)
        assert root_logger.level == logging.DEBUG

        # Clean up
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        root_logger.setLevel(logging.WARNING)

    def test_configure_logging_adds_handler(self) -> None:
        root_logger = logging.getLogger("harchos")
        initial_count = len(root_logger.handlers)

        configure_logging(level=logging.WARNING)
        assert len(root_logger.handlers) >= initial_count + 1

        # Clean up
        for handler in root_logger.handlers[initial_count:]:
            root_logger.removeHandler(handler)

    def test_configure_logging_custom_handler(self) -> None:
        root_logger = logging.getLogger("harchos")
        initial_count = len(root_logger.handlers)

        custom_handler = logging.StreamHandler()
        configure_logging(level=logging.DEBUG, handler=custom_handler)
        assert custom_handler in root_logger.handlers

        # Clean up
        root_logger.removeHandler(custom_handler)
        for handler in root_logger.handlers[initial_count - 1:]:
            root_logger.removeHandler(handler)
        root_logger.setLevel(logging.WARNING)
