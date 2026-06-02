"""
Contract: Port interface for Sketchfab asset API operations.

Defines the contract for Sketchfab-specific API calls (status, search,
preview, download). Separate from AssetProviderPort because these are
direct Blender-addon-mediated API wrappers, not generic adapters.
AES Port layer — depends only on taxonomy entities.
"""

from abc import ABC, abstractmethod

from taxonomy import AssetId, EnabledFlag, ImageBytes, ResultLimit, ScaleFactor, SearchQuery, StatusString


class SketchfabApiPort(ABC):
    """Port interface for direct Sketchfab API operations via Blender addon."""

    @abstractmethod
    def get_sketchfab_status(self) -> StatusString:
        """Check if Sketchfab integration is enabled in Blender."""
        pass

    @abstractmethod
    def search_sketchfab_models(
        self,
        query: SearchQuery,
        categories: SearchQuery | None = None,
        count: ResultLimit | None = None,
        downloadable: EnabledFlag | None = None,
    ) -> StatusString:
        """Search for models on Sketchfab with optional filtering."""
        pass

    @abstractmethod
    def get_sketchfab_model_preview(self, uid: AssetId) -> ImageBytes:
        """Get a preview thumbnail of a Sketchfab model by UID. Returns image bytes."""
        pass

    @abstractmethod
    def download_sketchfab_model(self, uid: AssetId, target_size: ScaleFactor) -> StatusString:
        """Download and import a Sketchfab model by its UID."""
        pass
