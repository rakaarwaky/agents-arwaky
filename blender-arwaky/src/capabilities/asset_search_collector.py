"""Collector: Multi-provider asset search and collection."""

import logging

from contract import AssetProviderPort, AssetSearchProtocol
from taxonomy import (
    AssetDownloadRequestVO,
    AssetId,
    AssetMetadata,
    AssetSearchRequestVO,
    ErrorMessage,
    FilePath,
    ImportedAsset,
    ObjectName,
    ProviderError,
    ProviderName,
    SearchQuery,
    StringList,
)

logger = logging.getLogger("BlenderMCPServer")


class AssetSearchCollector(AssetSearchProtocol):
    """Business logic for searching and managing assets across providers."""

    def __init__(self, providers: dict[str, AssetProviderPort]):
        self.providers = providers

    async def search_all(self, query: SearchQuery, providers: StringList | None = None) -> list[AssetMetadata]:
        """Search across all registered providers, optionally filtered."""
        all_results: list[AssetMetadata] = []
        for name, provider in self.providers.items():
            if providers is None or name in providers:
                try:
                    request = AssetSearchRequestVO(query=query)
                    response = await provider.search_assets(request)
                    all_results.extend(
                        AssetMetadata(
                            id=a.id,
                            name=a.name,
                            type=a.type,
                            provider=a.provider,
                            thumbnail_url=a.thumbnail_url,
                            tags=a.tags,
                        )
                        for a in response.assets
                    )
                except ProviderError as e:
                    logger.error(f"Error searching in {name}: {e}")
        return all_results

    async def fetch_and_import(self, provider_name: ProviderName, asset_id: AssetId) -> ImportedAsset:
        """Download from specific provider and import into Blender."""
        provider = self.providers.get(str(provider_name))
        if not provider:
            raise ProviderError(ErrorMessage(f"Provider {provider_name} not found"))

        try:
            request = AssetDownloadRequestVO(asset_id=asset_id, destination_path=FilePath(""))
            response = await provider.download_asset(request)
            if not response.file_path:
                raise ProviderError(ErrorMessage("Download returned no file path"))
            # Extract filename without extension as blender_id
            import os

            blender_id = os.path.splitext(os.path.basename(response.file_path))[0]
            return ImportedAsset(id=asset_id, name=ObjectName(str(asset_id)), blender_id=ObjectName(blender_id))
        except ProviderError as e:
            logger.error(f"Import failed for {asset_id} from {provider_name}: {e}")
            raise
