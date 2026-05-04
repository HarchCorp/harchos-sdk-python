"""Model (AI model) Pydantic models for the HarchOS SDK."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from .common import HarchOSBaseModel, ResourceMetadata
from .sovereignty import DataResidencyPolicy, SovereigntyLevel

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ModelStatus(str, Enum):
    """Status of an AI model in HarchOS."""

    AVAILABLE = "available"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    UNDEPLOYING = "undeploying"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class ModelFramework(str, Enum):
    """Supported ML frameworks."""

    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    ONNX = "onnx"
    JAX = "jax"
    CUSTOM = "custom"


class ModelTask(str, Enum):
    """Supported model tasks."""

    TEXT_GENERATION = "text_generation"
    TEXT_CLASSIFICATION = "text_classification"
    TOKEN_CLASSIFICATION = "token_classification"
    QUESTION_ANSWERING = "question_answering"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    IMAGE_GENERATION = "image_generation"
    IMAGE_CLASSIFICATION = "image_classification"
    SPEECH_RECOGNITION = "speech_recognition"
    EMBEDDINGS = "embeddings"
    MULTIMODAL = "multimodal"


# ---------------------------------------------------------------------------
# Model specifications
# ---------------------------------------------------------------------------

class ModelSize(HarchOSBaseModel):
    """Size information for an AI model."""

    parameters_billions: Optional[float] = Field(
        default=None, ge=0, description="Number of parameters in billions"
    )
    size_bytes: Optional[int] = Field(
        default=None, ge=0, description="Model size in bytes"
    )
    memory_required_gb: Optional[float] = Field(
        default=None, gt=0, description="Memory required to load the model (GB)"
    )


class ModelCapabilities(HarchOSBaseModel):
    """Capabilities and limits of an AI model."""

    max_context_length: int = Field(
        default=2048, gt=0, description="Maximum context window length in tokens"
    )
    max_output_tokens: int = Field(
        default=512, gt=0, description="Maximum output tokens per request"
    )
    supports_streaming: bool = Field(
        default=True, description="Whether the model supports streaming output"
    )
    supports_function_calling: bool = Field(
        default=False, description="Whether the model supports function calling"
    )
    supported_languages: List[str] = Field(
        default_factory=lambda: ["en"],
        description="Languages the model supports (ISO 639-1 codes)",
    )
    input_modalities: List[str] = Field(
        default_factory=lambda: ["text"],
        description="Supported input modalities (text, image, audio, video)",
    )
    output_modalities: List[str] = Field(
        default_factory=lambda: ["text"],
        description="Supported output modalities",
    )


# ---------------------------------------------------------------------------
# Model resource
# ---------------------------------------------------------------------------

class ModelSpec(HarchOSBaseModel):
    """Specification for creating or registering a model."""

    name: str = Field(..., min_length=1, max_length=128, description="Model name")
    framework: ModelFramework = Field(..., description="ML framework")
    task: ModelTask = Field(..., description="Primary task type")
    version: str = Field(default="1.0.0", description="Model version")
    description: Optional[str] = Field(default=None, description="Model description")
    size: Optional[ModelSize] = Field(default=None, description="Model size info")
    capabilities: Optional[ModelCapabilities] = Field(
        default=None, description="Model capabilities"
    )
    hub_id: Optional[str] = Field(
        default=None, description="Hub where the model is stored"
    )
    source_uri: Optional[str] = Field(
        default=None, description="URI to the model artifact"
    )
    sovereignty_level: SovereigntyLevel = Field(
        default=SovereigntyLevel.STRICT, description="Sovereignty level"
    )
    data_residency: Optional[DataResidencyPolicy] = Field(
        default=None, description="Data residency constraints"
    )
    labels: Dict[str, str] = Field(default_factory=dict, description="Custom labels")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate model name."""
        v = v.strip()
        if not v:
            raise ValueError("Model name must not be empty")
        return v

    @field_validator("version", mode="before")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version string."""
        v = v.strip()
        if not v:
            raise ValueError("Version must not be empty")
        return v


class Model(HarchOSBaseModel):
    """An AI model resource in HarchOS."""

    metadata: ResourceMetadata = Field(..., description="Resource metadata")
    spec: ModelSpec = Field(..., description="Model specification")
    status: ModelStatus = Field(
        default=ModelStatus.AVAILABLE, description="Current model status"
    )
    framework: ModelFramework = Field(..., description="ML framework")
    task: ModelTask = Field(..., description="Primary task")
    size: Optional[ModelSize] = Field(default=None, description="Model size info")
    capabilities: Optional[ModelCapabilities] = Field(
        default=None, description="Model capabilities"
    )
    deployed_at: Optional[datetime] = Field(
        default=None, description="When the model was last deployed"
    )
    inference_endpoint: Optional[str] = Field(
        default=None, description="URL for inference requests"
    )


class ModelList(HarchOSBaseModel):
    """A list of models with optional pagination info."""

    items: List[Model] = Field(default_factory=list, description="Model items")
    total: int = Field(default=0, ge=0, description="Total count")

    def to_dataframe(self) -> Any:
        """Convert model list to a pandas DataFrame.

        Requires the 'pandas' extra: pip install harchos[pandas]

        Raises:
            ImportError: If pandas is not installed
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for to_dataframe(). "
                "Install it with: pip install harchos[pandas]"
            ) from None
        return pd.DataFrame([item.model_dump() for item in self.items])
