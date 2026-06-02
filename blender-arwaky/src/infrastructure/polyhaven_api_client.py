"""PolyHaven asset integration tools"""

import logging

from contract import BlenderConnectionPort, PolyhavenApiPort
from taxonomy import ActionName, AssetId, AssetType, ExportFormat, ObjectName, ProviderName, SearchQuery, StatusString

logger = logging.getLogger("BlenderMCPServer")


class PolyhavenApiClient(PolyhavenApiPort):
    """Wrapper class for Polyhaven API functions."""

    _provider_ref: ProviderName = ProviderName("polyhaven")
    _asset_type_ref: AssetType = AssetType("all")

    def __init__(self, connection: BlenderConnectionPort):
        self._connection = connection

    def get_polyhaven_categories(self, asset_type: AssetType | None = None) -> StatusString:
        asset_type = asset_type or AssetType("hdris")
        """
        Get a list of categories for a specific asset type on Polyhaven.

        Parameters:
        - asset_type: The type of asset to get categories for (hdris, textures, models, all)
        """
        try:
            result = self._connection.send_command(
                ActionName("get_polyhaven_categories"), {"asset_type": str(asset_type)}
            )

            if "error" in result:
                return StatusString(f"Error: {result['error']}")

            # Format the categories in a more readable way
            categories = result["categories"]
            formatted_output = f"Categories for {asset_type}:\n\n"

            # Sort categories by count (descending)
            sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)

            for category, count in sorted_categories:
                formatted_output += f"- {category}: {count} assets\n"

            return StatusString(formatted_output)
        except Exception as e:
            logger.error(f"Error getting Polyhaven categories: {str(e)}")
            return StatusString(f"Error getting Polyhaven categories: {str(e)}")

    def search_polyhaven_assets(
        self, asset_type: AssetType | None = None, categories: SearchQuery | None = None
    ) -> StatusString:
        asset_type = asset_type or AssetType("all")
        """
        Search for assets on Polyhaven with optional filtering.

        Parameters:
        - asset_type: Type of assets to search for (hdris, textures, models, all)
        - categories: Optional comma-separated list of categories to filter by
        """
        try:
            result = self._connection.send_command(
                ActionName("search_polyhaven_assets"),
                {"asset_type": str(asset_type), "categories": str(categories) if categories is not None else None},
            )

            if "error" in result:
                return StatusString(f"Error: {result['error']}")

            assets = result["assets"]
            total_count = result["total_count"]
            returned_count = result["returned_count"]

            formatted_output = f"Found {total_count} assets"
            if categories:
                formatted_output += f" in categories: {categories}"
            formatted_output += f"\nShowing {returned_count} assets:\n\n"

            sorted_assets = sorted(assets.items(), key=lambda x: x[1].get("download_count", 0), reverse=True)

            for asset_id, asset_data in sorted_assets:
                formatted_output += f"- {asset_data.get('name', asset_id)} (ID: {asset_id})\n"
                formatted_output += f"  Type: {['HDRI', 'Texture', 'Model'][asset_data.get('type', 0)]}\n"
                formatted_output += f"  Categories: {', '.join(asset_data.get('categories', []))}\n"
                formatted_output += f"  Downloads: {asset_data.get('download_count', 'Unknown')}\n\n"

            return StatusString(formatted_output)
        except Exception as e:
            logger.error(f"Error searching Polyhaven assets: {str(e)}")
            return StatusString(f"Error searching Polyhaven assets: {str(e)}")

    def download_polyhaven_asset(
        self,
        asset_id: AssetId,
        asset_type: AssetType,
        resolution: StatusString | None = None,
        file_format: ExportFormat | None = None,
    ) -> StatusString:
        resolution = resolution or StatusString("1k")
        """
        Download and import a Polyhaven asset into Blender.

        Parameters:
        - asset_id: The ID of the asset to download
        - asset_type: The type of asset (hdris, textures, models)
        - resolution: The resolution to download (e.g., 1k, 2k, 4k)
        - file_format: Optional file format
        """
        try:
            result = self._connection.send_command(
                ActionName("download_polyhaven_asset"),
                {
                    "asset_id": str(asset_id),
                    "asset_type": str(asset_type),
                    "resolution": str(resolution),
                    "file_format": str(file_format) if file_format is not None else None,
                },
            )

            if "error" in result:
                return StatusString(f"Error: {result['error']}")

            if result.get("success"):
                message = result.get("message", "Asset downloaded and imported successfully")
                if str(asset_type) == "hdris":
                    return StatusString(f"{message}. The HDRI has been set as the world environment.")
                elif str(asset_type) == "textures":
                    material_name = result.get("material", "")
                    maps = ", ".join(result.get("maps", []))
                    return StatusString(f"{message}. Created material '{material_name}' with maps: {maps}.")
                elif str(asset_type) == "models":
                    return StatusString(f"{message}. The model has been imported into the current scene.")
                else:
                    return StatusString(message)
            else:
                return StatusString(f"Failed to download asset: {result.get('message', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Error downloading Polyhaven asset: {str(e)}")
            return StatusString(f"Error downloading Polyhaven asset: {str(e)}")

    def set_texture(self, object_name: ObjectName, texture_id: AssetId) -> StatusString:
        """
        Apply a previously downloaded Polyhaven texture to an object.

        Parameters:
        - object_name: Name of the object to apply the texture to
        - texture_id: ID of the Polyhaven texture to apply
        """
        try:
            result = self._connection.send_command(
                ActionName("set_texture"), {"object_name": str(object_name), "texture_id": str(texture_id)}
            )

            if "error" in result:
                return StatusString(f"Error: {result['error']}")

            if result.get("success"):
                material_name = result.get("material", "")
                maps = ", ".join(result.get("maps", []))
                material_info = result.get("material_info", {})
                node_count = material_info.get("node_count", 0)
                has_nodes = material_info.get("has_nodes", False)
                texture_nodes = material_info.get("texture_nodes", [])

                output = f"Successfully applied texture '{texture_id}' to {object_name}.\n"
                output += f"Using material '{material_name}' with maps: {maps}.\n\n"
                output += f"Material has nodes: {has_nodes}\n"
                output += f"Total node count: {node_count}\n\n"
                if texture_nodes:
                    output += "Texture nodes:\n"
                    for node in texture_nodes:
                        output += f"- {node['name']} using image: {node['image']}\n"
                        if node["connections"]:
                            output += "  Connections:\n"
                            for conn in node["connections"]:
                                output += f"    {conn}\n"
                else:
                    output += "No texture nodes found in the material.\n"
                return StatusString(output)
            else:
                return StatusString(f"Failed to apply texture: {result.get('message', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Error applying texture: {str(e)}")
            return StatusString(f"Error applying texture: {str(e)}")

    def get_polyhaven_status(self) -> StatusString:
        """
        Check if PolyHaven integration is enabled in Blender.
        """
        try:
            result = self._connection.send_command(ActionName("get_polyhaven_status"))
            enabled = result.get("enabled", False)
            message = result.get("message", "")
            if enabled:
                message += "PolyHaven is good at Textures, and has a wider variety of textures than Sketchfab."
            return StatusString(message)
        except Exception as e:
            logger.error(f"Error checking PolyHaven status: {str(e)}")
            return StatusString(f"Error checking PolyHaven status: {str(e)}")


# PolyhavenApiClient is now purely a technical implementation that depends on a connection port.
# Module-level entry points have been moved to infrastructure/__init__.py or similar.
