"""
Contract: Port interface for Polyhaven asset API operations.

Defines the contract for Polyhaven-specific API calls (categories, search,
download, texture application). Separate from AssetProviderPort because
these are direct Blender-addon-mediated API wrappers, not generic adapters.
AES Port layer — depends only on taxonomy entities.
"""

from abc import ABC, abstractmethod

from taxonomy import AssetId, AssetType, ExportFormat, ObjectName, SearchQuery, StatusString


class PolyhavenApiPort(ABC):
    """Port interface for direct Polyhaven API operations via Blender addon."""

    @abstractmethod
    def get_polyhaven_categories(self, asset_type: AssetType | None = None) -> StatusString:
        """Get categories for a specific asset type on Polyhaven."""
        pass

    @abstractmethod
    def search_polyhaven_assets(
        self, asset_type: AssetType | None = None, categories: SearchQuery | None = None
    ) -> StatusString:
        """Search for assets on Polyhaven with optional filtering."""
        pass

    @abstractmethod
    def download_polyhaven_asset(
        self,
        asset_id: AssetId,
        asset_type: AssetType,
        resolution: StatusString | None = None,
        file_format: ExportFormat | None = None,
    ) -> StatusString:
        """Download and import a Polyhaven asset into Blender."""
        pass

    @abstractmethod
    def set_texture(self, object_name: ObjectName, texture_id: AssetId) -> StatusString:
        """Apply a downloaded Polyhaven texture to an object."""
        pass

    @abstractmethod
    def get_polyhaven_status(self) -> StatusString:
        """Check if Polyhaven integration is enabled."""
        pass
