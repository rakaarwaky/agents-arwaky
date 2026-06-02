"""
Contract: Provider VO — Consolidated DTOs for Asset Search, Download, and Generation.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from .blender_spatial_vo import Vector3D
from .core_types_vo import (
    AssetCount,
    AssetId,
    AssetName,
    AssetType,
    AssetTypeFilter,
    ErrorMessage,
    FilePath,
    JobId,
    JobState,
    NextPageToken,
    ObjectName,
    Progress,
    Prompt,
    ProviderName,
    ResultLimit,
    SearchQuery,
    SuccessFlag,
    TagList,
    ThumbnailUrl,
)


class ProviderVO:
    """Abstract base class grounded by all Provider VO DTOs."""

    _contract_name: str = "ProviderVO"

    @classmethod
    def get_contract_name(cls) -> str:
        return cls._contract_name

    def to_request_dict(self) -> dict:
        return {}


# ============== Asset Search & Download ==============


class AssetSearchRequestVO(ProviderVO, BaseModel):
    """Input DTO for asset search operations."""

    query: SearchQuery = Field(..., min_length=1, max_length=200)
    asset_type: AssetTypeFilter | None = Field(default=AssetTypeFilter("all"))
    categories: TagList | None = Field(default_factory=lambda: TagList([]))
    limit: ResultLimit = Field(default=ResultLimit(10))
    provider: ProviderName | None = Field(default=None)

    @field_validator("query")
    @classmethod
    def query_not_just_spaces(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty or whitespace")
        return v


class AssetMetadataVO(BaseModel):
    """Asset metadata DTO."""

    id: AssetId = Field(...)
    name: AssetName = Field(...)
    type: AssetType = Field(...)
    thumbnail_url: ThumbnailUrl | None = Field(None)
    tags: TagList = Field(default_factory=lambda: TagList([]))
    provider: ProviderName = Field(...)


class AssetSearchResponseVO(ProviderVO, BaseModel):
    """Output DTO for asset search results."""

    assets: list[AssetMetadataVO] = Field(default_factory=list)
    total: AssetCount = Field(AssetCount(0))
    next_token: NextPageToken | None = Field(None)
    provider: ProviderName = Field(...)


class AssetDownloadRequestVO(ProviderVO, BaseModel):
    """Request DTO for downloading an asset."""

    asset_id: AssetId = Field(...)
    destination_path: FilePath = Field(...)


class AssetDownloadResponseVO(ProviderVO, BaseModel):
    """Response DTO for asset download result."""

    success: SuccessFlag = Field(...)
    file_path: FilePath | None = Field(None)
    message: ErrorMessage | None = Field(None)


# ============== AI Generation ==============


class GenerationStartRequestVO(ProviderVO, BaseModel):
    """Request to start a generation job."""

    prompt: Prompt = Field(...)


class GenerationStartResponseVO(ProviderVO, BaseModel):
    """Response after starting generation."""

    job_id: JobId = Field(...)
    status: JobState = Field(...)


class GenerationStatusRequestVO(ProviderVO, BaseModel):
    """Request to poll generation job status."""

    job_id: JobId = Field(...)


class GenerationStatusResponseVO(ProviderVO, BaseModel):
    """Response with current generation progress."""

    job_id: JobId = Field(...)
    status: JobState = Field(...)
    progress: Progress = Field(Progress(0.0))
    error: ErrorMessage | None = Field(None)


class ImportGeneratedAssetRequestVO(ProviderVO, BaseModel):
    """Request to import a completed generation result."""

    asset_id: AssetId = Field(...)
    object_name: ObjectName = Field(...)
    location: Vector3D = Field(...)
    rotation: Vector3D | None = Field(None)
    scale: Vector3D | None = Field(None)


class ImportGeneratedAssetResponseVO(ProviderVO, BaseModel):
    """Response after importing generated asset."""

    success: SuccessFlag = Field(...)
    object_name: ObjectName = Field(...)
    blender_id: ObjectName = Field(...)
    message: ErrorMessage | None = Field(None)
