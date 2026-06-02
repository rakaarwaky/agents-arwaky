"""
Contract: Asset Search Contract (ABC based).
"""

from abc import ABC, abstractmethod

from taxonomy import AssetId, AssetMetadata, ImportedAsset, ProviderName, SearchQuery, StringList


class AssetSearchProtocol(ABC):
    """Business logic interface for asset searching and importing."""

    @abstractmethod
    async def search_all(self, query: SearchQuery, providers: StringList | None = None) -> list[AssetMetadata]:
        """Search across all registered providers, optionally filtered."""
        pass

    @abstractmethod
    async def fetch_and_import(self, provider_name: ProviderName, asset_id: AssetId) -> ImportedAsset:
        """Download from specific provider and import into Blender."""
        pass
