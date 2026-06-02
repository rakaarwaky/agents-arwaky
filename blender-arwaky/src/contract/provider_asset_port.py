"""
Contract: Port interface for asset providers (Polyhaven, Sketchfab, etc.).

Defines the contract for searching, retrieving details, and downloading assets.
AES Port layer — depends only on taxonomy entities and provider IO DTOs.
"""

from abc import ABC, abstractmethod

from taxonomy import (
    AssetDownloadRequestVO,
    AssetDownloadResponseVO,
    AssetId,
    AssetMetadata,
    AssetSearchRequestVO,
    AssetSearchResponseVO,
)


class AssetProviderPort(ABC):
    """Port interface for asset provider services."""

    @abstractmethod
    async def search_assets(self, request: AssetSearchRequestVO) -> AssetSearchResponseVO:
        """Search for assets matching the query. Returns paginated results."""
        pass

    @abstractmethod
    async def get_asset_details(self, asset_id: AssetId) -> AssetMetadata | None:
        """Get detailed metadata for a specific asset."""
        pass

    @abstractmethod
    async def download_asset(self, request: AssetDownloadRequestVO) -> AssetDownloadResponseVO:
        """Download an asset to the specified destination. Returns download result."""
        pass
