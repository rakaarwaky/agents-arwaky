"""
Infrastructure: Adapter for Polyhaven Asset Provider.
"""

import logging
from typing import cast

from contract import (
    AssetProviderPort,
    BlenderConnectionPort,
)
from taxonomy import (
    ActionName,
    AssetCount,
    AssetDownloadRequestVO,
    AssetDownloadResponseVO,
    AssetId,
    AssetMetadata,
    AssetMetadataVO,
    AssetName,
    AssetSearchRequestVO,
    AssetSearchResponseVO,
    AssetType,
    ErrorMessage,
    FilePath,
    ProviderError,
    ProviderName,
    SuccessFlag,
    TagList,
)

logger = logging.getLogger("BlenderMCPServer")


class PolyhavenAssetAdapter(AssetProviderPort):
    """Implementation of AssetProviderPort for Polyhaven."""

    def __init__(self, connection_port: BlenderConnectionPort):
        self._connection = connection_port
        self.provider_name = "Polyhaven"

    def _get_conn(self):
        """Internal helper for connection access."""
        if not self._connection:
            raise ProviderError(ErrorMessage("Blender connection not initialized"))
        return self._connection

    async def search_assets(self, request: AssetSearchRequestVO) -> AssetSearchResponseVO:
        try:
            conn = self._get_conn()

            result = conn.send_command(
                ActionName("search_polyhaven_assets"),
                {"asset_type": request.asset_type or "all", "categories": request.categories},
            )

            assets = []
            for asset_id, data in result.get("assets", {}).items():
                assets.append(
                    AssetMetadata(
                        id=AssetId(asset_id),
                        name=AssetName(data.get("name", asset_id)),
                        type=AssetType(str(data.get("type", "unknown"))),
                        provider=ProviderName(self.provider_name),
                        tags=cast(TagList, data.get("categories", [])),
                    )
                )
            return AssetSearchResponseVO(
                assets=[
                    AssetMetadataVO(
                        id=a.id,
                        name=a.name,
                        type=a.type,
                        provider=ProviderName(a.provider),
                        tags=a.tags,
                        thumbnail_url=None,
                    )
                    for a in assets
                ],
                total=AssetCount(len(assets)),
                next_token=None,
                provider=ProviderName(self.provider_name),
            )
        except Exception as e:
            logger.error(f"Polyhaven search error: {str(e)}")
            raise ProviderError(ErrorMessage(str(e))) from e

    async def get_asset_details(self, asset_id: str) -> AssetMetadata | None:
        """Get detailed info for a Polyhaven asset."""
        try:
            conn = self._get_conn()
            result = conn.send_command(ActionName("get_polyhaven_asset_details"), {"asset_id": asset_id})
            if isinstance(result, dict) and "error" in result:
                logger.warning("Polyhaven get_asset_details error: %s", result["error"])
                return None
            tags = cast(TagList, result.get("tags", []) + result.get("categories", []))
            return AssetMetadata(
                id=AssetId(asset_id),
                name=AssetName(result.get("name", asset_id)),
                type=AssetType(result.get("type", "unknown")),
                provider=ProviderName(self.provider_name),
                tags=tags,
            )
        except Exception as e:
            logger.error(f"Polyhaven details error: {str(e)}")
            return None

    async def download_asset(self, request: AssetDownloadRequestVO) -> AssetDownloadResponseVO:
        try:
            conn = self._get_conn()
            asset_type = "models"
            result = conn.send_command(
                ActionName("download_polyhaven_asset"), {"asset_id": request.asset_id, "asset_type": asset_type}
            )
            if not result.get("success"):
                raise ProviderError(ErrorMessage(result.get("message", "Download failed")))
            return AssetDownloadResponseVO(
                success=SuccessFlag(True),
                file_path=FilePath(result.get("path", "")),
                message=ErrorMessage("Download successful"),
            )
        except Exception as e:
            logger.error(f"Polyhaven download error: {str(e)}")
            raise ProviderError(ErrorMessage(str(e))) from e
