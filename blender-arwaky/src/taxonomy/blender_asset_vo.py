from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, cast

from .core_types_vo import AssetId, AssetName, AssetType, ObjectName, ProviderName, TagList, ThumbnailUrl

# ============================================================
# ASSET CONSTANTS
# ============================================================

ASSET_TYPE_HDRIS: Final[AssetType] = AssetType("hdris")
ASSET_TYPE_TEXTURES: Final[AssetType] = AssetType("textures")
ASSET_TYPE_MODELS: Final[AssetType] = AssetType("models")

PROVIDER_POLYHAVEN: Final[ProviderName] = ProviderName("tool_search_polyhaven")
PROVIDER_SKETCHFAB: Final[ProviderName] = ProviderName("tool_search_sketchfab")


# ============================================================
# ASSET VALUE OBJECTS
# ============================================================


@dataclass(frozen=True)
class AssetMetadata:
    """Immutable metadata for an asset from a provider."""

    id: AssetId
    name: AssetName
    type: AssetType  # "hdris", "textures", "model"
    provider: ProviderName
    thumbnail_url: ThumbnailUrl | None = None
    tags: TagList = field(default_factory=lambda: cast(TagList, []))


@dataclass(frozen=True)
class ImportedAsset:
    """Result of importing an asset into Blender."""

    id: AssetId
    name: ObjectName
    blender_id: ObjectName  # Blender internal object name


# ============================================================
# ASSET FACTORIES
# ============================================================


def create_asset_id(raw: str) -> AssetId:
    return AssetId(raw)


def create_provider_name(raw: str) -> ProviderName:
    return ProviderName(raw)
