"""
AssetExpert: Handles asset discovery, retrieval, and placement.
Supports Polyhaven, Sketchfab, and AI-generated assets.
"""

import logging

from contract import AssetSearchProtocol, GenerationProtocol, SceneOperateProtocol, SearchExpertOrchestratorAggregate
from taxonomy import (
    AssetId,
    Prompt,
    ProviderName,
    PythonCode,
    SearchQuery,
    StatusString,
    StringList,
)

from .agent_logic_coordinator import ExpertOrchestratorLogic

logger = logging.getLogger("BlenderMCPServer.Agents")


class SearchExpertOrchestrator(ExpertOrchestratorLogic, SearchExpertOrchestratorAggregate):
    """
    Specialist for asset operations:
    - Search across all providers
    - Import & place assets
    - AI generation when assets not found
    - Asset validation & quality check
    """

    _contract_name: StatusString = StatusString("SearchExpertOrchestrator")

    def __init__(
        self,
        asset_mgr: AssetSearchProtocol,
        generation_mgr: GenerationProtocol,
        blender_mgr: SceneOperateProtocol,
    ):
        super().__init__("SearchExpertOrchestrator")
        self.assets = asset_mgr
        self.generation = generation_mgr
        self.blender = blender_mgr

    async def execute(self, action: str, params: dict[str, object] | None = None) -> dict[str, object]:
        if params is None:
            params = {}

        self.log_info(f"Action: {action}, params: {params}")

        try:
            if action == "search":
                return await self._handle_search(params)
            elif action == "import":
                return await self._handle_import(params)
            elif action == "place":
                return await self._handle_place(params)
            elif action == "generate_if_missing":
                return await self._handle_generate_if_missing(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            self.log_error(f"AssetExpert failed: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_search(self, params: dict[str, object]) -> dict[str, object]:
        """Handle search action across all providers."""
        query = str(params.get("query", ""))
        providers_param = params.get("providers")
        providers = StringList([str(p) for p in providers_param]) if isinstance(providers_param, list) else None
        results = await self.assets.search_all(SearchQuery(query), providers)
        return {
            "success": True,
            "count": len(results),
            "assets": [
                {
                    "id": str(a.id),
                    "name": str(a.name),
                    "provider": str(a.provider),
                    "type": str(a.type),
                    "preview_url": str(a.thumbnail_url) if a.thumbnail_url else "",
                }
                for a in results
            ],
        }

    async def _handle_import(self, params: dict[str, object]) -> dict[str, object]:
        """Handle import action to fetch and import an asset."""
        provider = params.get("provider")
        asset_id = params.get("asset_id")
        if not provider or not asset_id:
            return {"success": False, "error": "provider and asset_id required"}

        provider_name = ProviderName(str(provider))
        asset_id_vo = AssetId(str(asset_id))
        asset = await self.assets.fetch_and_import(provider_name, asset_id_vo)
        return {
            "success": True,
            "asset": {
                "id": str(asset.id),
                "name": str(asset.name),
                "blender_id": str(asset.blender_id),
            },
        }

    async def _handle_place(self, params: dict[str, object]) -> dict[str, object]:
        """Handle place action to position an asset in the scene."""
        asset_id = params.get("asset_id")
        location_val = params.get("location")
        location = location_val if isinstance(location_val, list) else [0.0, 0.0, 0.0]

        if not asset_id:
            return {"success": False, "error": "asset_id required"}

        # Place the asset by executing Blender Python code directly
        place_code = (
            "import bpy\n"
            "for obj in bpy.context.selected_objects:\n"
            f"    obj.location = ({location[0]}, {location[1]}, {location[2]})\n"
        )
        result = await self.blender.blender.execute_code(PythonCode(place_code))
        return {
            "success": True,
            "message": f"Asset {asset_id} placed at {location}",
            "result": str(result),
        }

    async def _handle_generate_if_missing(self, params: dict[str, object]) -> dict[str, object]:
        """AI-generate asset if search yields no results."""
        query = str(params.get("query", ""))
        provider = str(params.get("ai_provider", "tool_generate_hyper3d"))

        # Try search first
        results = await self.assets.search_all(SearchQuery(query))
        if results:
            return {
                "success": True,
                "action": "search_found",
                "count": len(results),
                "assets": [str(r.id) for r in results],
            }

        # Generate via AI
        self.log_info(f"No assets found for '{query}', generating via {provider}...")
        job_id = await self.generation.start_generation(ProviderName(provider), Prompt(query))
        return {
            "success": True,
            "action": "generation_started",
            "provider": provider,
            "job_id": str(job_id),
            "message": f"AI generation initiated for '{query}'",
        }
