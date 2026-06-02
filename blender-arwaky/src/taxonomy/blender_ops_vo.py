"""
Contract: Blender Operations VO — Consolidated DTOs for Blender manipulation.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from .blender_object_entity import BlenderObject
from .blender_scene_entity import SceneInfo
from .core_types_vo import (
    AssetId,
    CleanupMode,
    CoordinateList,
    ExportFormat,
    FilePath,
    HdriId,
    ImageFormat,
    LightStrength,
    MaterialName,
    MaxSize,
    ModifierName,
    ObjectCount,
    ObjectName,
    PrimitiveType,
    RenderEngine,
    ResolutionX,
    ResolutionY,
    SampleCount,
    SuccessFlag,
)


class BlenderOpsVO:
    """Abstract base class grounded by all BlenderOps VO DTOs."""

    _contract_name: str = "BlenderOpsVO"

    @classmethod
    def get_contract_name(cls) -> str:
        return cls._contract_name

    def to_request_dict(self) -> dict:
        return {}


# ============== Scene VO ==============


class CleanupSceneRequestVO(BlenderOpsVO, BaseModel):
    """Input DTO for cleanup_scene operation."""

    mode: CleanupMode = Field(default=CleanupMode("all"), description="Cleanup mode: 'all', 'objects', 'meshes'")

    @field_validator("mode")
    @classmethod
    def mode_valid(cls, v: str) -> str:
        allowed = {"all", "objects", "meshes"}
        if v not in allowed:
            raise ValueError(f"mode must be one of {allowed}")
        return v


class CleanupSceneResponseVO(BlenderOpsVO, BaseModel):
    """Output DTO from cleanup_scene operation."""

    success: SuccessFlag = Field(..., description="Whether cleanup was successful")
    objects_removed: ObjectCount = Field(..., description="Number of objects removed")
    message: str | None = Field(None, description="Optional status message")


class SetupEnvironmentRequestVO(BaseModel):
    """Input DTO for setup environment (HDRI)."""

    hdri_id: HdriId = Field(..., min_length=1, description="Polyhaven HDRI Asset ID")
    strength: LightStrength = Field(
        default=LightStrength(1.0), ge=0.0, le=10.0, description="Environment light strength"
    )


class SetupEnvironmentResponseVO(BaseModel):
    """Output DTO from setup environment."""

    success: SuccessFlag = Field(..., description="Whether setup was successful")
    hdri_path: FilePath | None = Field(None, description="Path of the downloaded HDRI file")
    message: str | None = Field(None, description="Optional status message")


class GetSceneInfoRequestVO(BlenderOpsVO, BaseModel):
    """Input DTO for get_scene_info."""

    _contract_name: str = "GetSceneInfoRequestVO"


class GetSceneInfoResponseVO(BaseModel):
    """Output DTO from get_scene_info."""

    success: SuccessFlag = Field(..., description="Whether query was successful")
    scene_info: SceneInfo | None = Field(None, description="Complete scene information")
    message: str | None = Field(None, description="Optional status message")


# ============== Object VO ==============


class PlaceAssetRequestVO(BaseModel):
    """Input DTO for place_asset (import & position asset)."""

    asset_id: AssetId = Field(..., min_length=1, description="Asset ID")
    object_name: ObjectName | None = Field(None, description="Blender object name")
    location: CoordinateList = Field(..., min_length=3, max_length=3)
    scale: CoordinateList | None = Field(None, min_length=3, max_length=3)
    rotation: CoordinateList | None = Field(None, min_length=3, max_length=3)

    @field_validator("location", "scale", "rotation")
    @classmethod
    def validate_coord(cls, v, info):
        if v is not None and len(v) != 3:
            raise ValueError(f"{info.field_name} must have exactly 3 elements")
        return v


class PlaceAssetResponseVO(BaseModel):
    """Output DTO from place_asset."""

    success: SuccessFlag = Field(..., description="Whether placement was successful")
    object_name: ObjectName = Field(..., description="Name of created object")
    asset_id: AssetId = Field(..., description="Source Asset ID")
    location: CoordinateList = Field(..., description="Final location")
    message: str | None = Field(None, description="Optional status message")


class GetObjectInfoRequestVO(BaseModel):
    """Input DTO for get_object_info."""

    object_name: ObjectName = Field(..., description="Name of object")


class GetObjectInfoResponseVO(BaseModel):
    """Output DTO from get_object_info."""

    success: SuccessFlag = Field(..., description="Whether query was successful")
    object_info: BlenderObject | None = Field(None, description="Object data")
    message: str | None = Field(None, description="Optional status message")


class SetObjectTransformRequestVO(BaseModel):
    """Input DTO for set object transform."""

    object_name: ObjectName = Field(..., description="Target object name")
    location: CoordinateList | None = Field(None, min_length=3, max_length=3)
    rotation: CoordinateList | None = Field(None, min_length=3, max_length=3)
    scale: CoordinateList | None = Field(None, min_length=3, max_length=3)


class SetObjectTransformResponseVO(BaseModel):
    """Output DTO from set transform."""

    success: SuccessFlag = Field(..., description="Whether transform apply was successful")
    object_name: ObjectName = Field(..., description="Name of modified object")
    message: str | None = Field(None, description="Optional status message")


class DeleteObjectRequestVO(BaseModel):
    """Input DTO for delete object."""

    object_name: ObjectName = Field(..., description="Name of object to delete")


class DeleteObjectResponseVO(BaseModel):
    """Output DTO from delete object."""

    success: SuccessFlag = Field(..., description="Whether delete was successful")
    object_name: ObjectName = Field(..., description="Name of deleted object")
    message: str | None = Field(None, description="Optional status message")


class CreatePrimitiveRequestVO(BaseModel):
    """Input DTO for creating primitive."""

    primitive_type: PrimitiveType = Field(..., description="Primitive type")
    location: CoordinateList | None = Field(None, min_length=3, max_length=3)
    scale: CoordinateList | None = Field(None, min_length=3, max_length=3)
    name: ObjectName | None = Field(None)


class CreatePrimitiveResponseVO(BaseModel):
    """Output DTO from create primitive."""

    success: SuccessFlag = Field(..., description="Whether creation was successful")
    object_name: ObjectName = Field(..., description="Name of created object")
    primitive_type: PrimitiveType = Field(...)
    message: str | None = Field(None)


class SetMaterialRequestVO(BaseModel):
    """Input DTO for setting material."""

    object_name: ObjectName = Field(...)
    material_name: MaterialName = Field(...)


class SetMaterialResponseVO(BaseModel):
    """Output DTO from set material."""

    success: SuccessFlag = Field(...)
    object_name: ObjectName = Field(...)
    material_name: MaterialName = Field(...)
    message: str | None = Field(None)


class ApplyModifierRequestVO(BaseModel):
    """Input DTO for applying modifier."""

    object_name: ObjectName = Field(...)
    modifier_name: ModifierName = Field(...)


class ApplyModifierResponseVO(BaseModel):
    """Output DTO from apply modifier."""

    success: SuccessFlag = Field(...)
    object_name: ObjectName = Field(...)
    modifier_name: ModifierName = Field(...)
    message: str | None = Field(None)


# ============== Render VO ==============


class RenderRequestVO(BaseModel):
    """Input DTO for render operation."""

    output_path: FilePath = Field(...)
    resolution_x: ResolutionX = Field(default=ResolutionX(1920))
    resolution_y: ResolutionY = Field(default=ResolutionY(1080))
    render_engine: RenderEngine | None = Field(None)
    samples: SampleCount | None = Field(None)


class RenderResponseVO(BaseModel):
    """Output DTO from render operation."""

    success: SuccessFlag = Field(...)
    image_path: FilePath | None = Field(None)
    render_time: float | None = Field(None)
    message: str | None = Field(None)


class GetScreenshotRequestVO(BaseModel):
    """Input DTO for capturing viewport screenshot."""

    max_size: MaxSize = Field(default=MaxSize(800))
    format: ImageFormat | None = Field(default=ImageFormat("png"))


class ScreenshotResponseVO(BaseModel):
    """Output DTO from get_viewport_screenshot."""

    success: SuccessFlag = Field(...)
    image_data: bytes = Field(...)
    format: ImageFormat = Field(...)
    width: ResolutionX = Field(...)
    height: ResolutionY = Field(...)


# ============== Import/Export VO ==============


class ImportGlbRequestVO(BaseModel):
    """Input DTO for importing GLB/GLTF."""

    file_path: FilePath = Field(...)
    object_name: ObjectName | None = Field(None)


class ImportGlbResponseVO(BaseModel):
    """Output DTO from import GLB."""

    success: SuccessFlag = Field(...)
    object_name: ObjectName = Field(...)
    file_path: FilePath = Field(...)
    message: str | None = Field(None)


class ExportModelRequestVO(BaseModel):
    """Input DTO for exporting model."""

    object_name: ObjectName = Field(...)
    file_path: FilePath = Field(...)
    export_format: ExportFormat = Field(default=ExportFormat("glb"))


class ExportModelResponseVO(BaseModel):
    """Output DTO from export model."""

    success: SuccessFlag = Field(...)
    file_path: FilePath = Field(...)
    object_name: ObjectName = Field(...)
    message: str | None = Field(None)
