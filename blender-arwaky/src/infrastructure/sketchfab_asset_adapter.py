"""
Infrastructure: Adapter for Sketchfab Asset Provider.
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
    AssetId,
    AssetMetadata,
    AssetName,
    AssetType,
    ErrorMessage,
    FilePath,
    ProviderError,
    ProviderName,
    SuccessFlag,
    TagList,
)
from taxonomy import (
    AssetDownloadRequestVO as AssetDownloadRequestIO,
)
from taxonomy import (
    AssetDownloadResponseVO as AssetDownloadResponseIO,
)
from taxonomy import (
    AssetMetadataVO as AssetMetadataIO,
)
from taxonomy import (
    AssetSearchRequestVO as AssetSearchRequestIO,
)
from taxonomy import (
    AssetSearchResponseVO as AssetSearchResponseIO,
)

logger = logging.getLogger("BlenderMCPServer")


class SketchfabAssetAdapter(AssetProviderPort):
    """Implementation of AssetProviderPort for Sketchfab."""

    def __init__(self, connection: BlenderConnectionPort):
        self.provider_name = "Sketchfab"
        self._connection = connection

    def _get_conn(self) -> BlenderConnectionPort:
        return self._connection

    async def search_assets(self, request: AssetSearchRequestIO) -> AssetSearchResponseIO:
        try:
            conn = self._get_conn()

            result = conn.send_command(
                ActionName("search_sketchfab_models"), {"query": request.query, "count": 20, "downloadable": True}
            )

            assets = []
            for model in result.get("results", []):
                assets.append(
                    AssetMetadata(
                        id=AssetId(model.get("uid", "")),
                        name=AssetName(model.get("name", "Unnamed model")),
                        type=AssetType("model"),
                        provider=ProviderName(self.provider_name),
                        tags=cast(TagList, []),
                    )
                )
            return AssetSearchResponseIO(
                assets=[
                    AssetMetadataIO(
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
            logger.error(f"Sketchfab search error: {str(e)}")
            raise ProviderError(ErrorMessage(str(e))) from e

    async def get_asset_details(self, asset_id: str) -> AssetMetadata | None:
        """Get detailed info for a Sketchfab model."""
        try:
            conn = self._get_conn()
            result = conn.send_command(ActionName("get_sketchfab_model_preview"), {"uid": asset_id})
            if isinstance(result, dict) and "error" in result:
                logger.warning("Sketchfab get_asset_details error: %s", result["error"])
                return None
            return AssetMetadata(
                id=AssetId(asset_id),
                name=AssetName(result.get("model_name", asset_id)),
                type=AssetType("model"),
                provider=ProviderName(self.provider_name),
                tags=cast(TagList, []),
            )
        except Exception as e:
            logger.error(f"Sketchfab details error: {str(e)}")
            return None

    async def download_asset(self, request: AssetDownloadRequestIO) -> AssetDownloadResponseIO:
        try:
            conn = self._get_conn()
            target_size = 1.0
            result = conn.send_command(
                ActionName("download_sketchfab_model"),
                {"uid": request.asset_id, "normalize_size": True, "target_size": target_size},
            )
            if not result.get("success"):
                raise ProviderError(ErrorMessage(result.get("message", "Download failed")))
            return AssetDownloadResponseIO(
                success=SuccessFlag(True),
                file_path=FilePath(",".join(result.get("imported_objects", []))),
                message=ErrorMessage("Download successful"),
            )
        except Exception as e:
            logger.error(f"Sketchfab download error: {str(e)}")
            raise ProviderError(ErrorMessage(str(e))) from e
