"""Sketchfab model integration tools"""

import base64
import logging

from contract import BlenderConnectionPort, SketchfabApiPort
from taxonomy import (
    ActionName,
    AssetId,
    AssetType,
    EnabledFlag,
    ErrorMessage,
    ImageBytes,
    ProviderError,
    ProviderName,
    ResultLimit,
    ScaleFactor,
    SearchQuery,
    StatusString,
)

logger = logging.getLogger("BlenderMCPServer")


class SketchfabApiClient(SketchfabApiPort):
    """Wrapper class for Sketchfab API functions."""

    _provider_ref: ProviderName = ProviderName("sketchfab")
    _asset_type_ref: AssetType = AssetType("model")

    def __init__(self, connection: BlenderConnectionPort):
        """Initialize with an explicit connection port."""
        self._connection = connection

    @property
    def connection(self) -> BlenderConnectionPort:
        return self._connection

    def get_sketchfab_status(self) -> StatusString:
        """
        Check if Sketchfab integration is enabled in Blender.
        Returns a message indicating whether Sketchfab features are available.
        """
        try:
            blender = self.connection
            result = blender.send_command(ActionName("get_sketchfab_status"))
            enabled = result.get("enabled", False)
            message = result.get("message", "")
            if enabled:
                message += "Sketchfab is good at Realistic model_domain_entity_model, and has a wider variety of model_domain_entity_model than PolyHaven."
                return StatusString(message)
            return StatusString(message or "Sketchfab integration is not enabled")
        except Exception as e:
            logger.error(f"Error checking Sketchfab status: {str(e)}")
            return StatusString(f"Error checking Sketchfab status: {str(e)}")

    @staticmethod
    def _format_search_results(model_list: list, query: str) -> str:
        """Format a list of Sketchfab model results into a readable string."""
        if not model_list:
            return f"No model_domain_entity_model found matching '{query}'"

        formatted_output = f"Found {len(model_list)} model_domain_entity_model matching '{query}':\n\n"

        for model in model_list:
            if model is None:
                continue

            model_name = model.get("name", "Unnamed model")
            model_uid = model.get("uid", "Unknown ID")
            formatted_output += f"- {model_name} (UID: {model_uid})\n"

            # Get user info with safety checks
            user = model.get("user") or {}
            username = user.get("username", "Unknown author") if isinstance(user, dict) else "Unknown author"
            formatted_output += f"  Author: {username}\n"

            # Get license info with safety checks
            license_data = model.get("license") or {}
            license_label = license_data.get("label", "Unknown") if isinstance(license_data, dict) else "Unknown"
            formatted_output += f"  License: {license_label}\n"

            # Add face count and downloadable status
            face_count = model.get("faceCount", "Unknown")
            is_downloadable = "Yes" if model.get("isDownloadable") else "No"
            formatted_output += f"  Face count: {face_count}\n"
            formatted_output += f"  Downloadable: {is_downloadable}\n\n"

        return formatted_output

    def search_sketchfab_models(
        self,
        query: SearchQuery,
        categories: SearchQuery | None = None,
        count: ResultLimit | None = None,
        downloadable: EnabledFlag | None = None,
    ) -> StatusString:
        count = count or ResultLimit(20)
        downloadable = downloadable or EnabledFlag(True)
        """
        Search for model_domain_entity_model on Sketchfab with optional filtering.

        Parameters:
        - query: Text to search for
        - categories: Optional comma-separated list of categories
        - count: Maximum number of results to return (default 20)
        - downloadable: Whether to include only downloadable model_domain_entity_model (default True)

        Returns a formatted list of matching model_domain_entity_model.
        """
        try:
            blender = self.connection
            logger.info(
                f"Searching Sketchfab model_domain_entity_model with query: {query}, categories: {categories}, count: {count}, downloadable: {downloadable}"
            )
            result = blender.send_command(
                ActionName("search_sketchfab_models"),
                {
                    "query": str(query),
                    "categories": str(categories) if categories is not None else None,
                    "count": int(count),
                    "downloadable": bool(downloadable),
                },
            )

            if result is None:
                logger.error("Received None result from Sketchfab search")
                return StatusString("Error: Received no response from Sketchfab search")

            if "error" in result:
                logger.error(f"Error from Sketchfab search: {result['error']}")
                return StatusString(f"Error: {result['error']}")

            # Format the results
            model_domain_entity_model = result.get("results", []) or []
            return StatusString(self._format_search_results(model_domain_entity_model, str(query)))
        except Exception as e:
            logger.error(f"Error searching Sketchfab model_domain_entity_model: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
            return StatusString(f"Error searching Sketchfab model_domain_entity_model: {str(e)}")

    def get_sketchfab_model_preview(self, uid: AssetId) -> ImageBytes:
        """
        Get a preview thumbnail of a Sketchfab model by its UID.
        Use this to visually confirm a model before downloading.

        Parameters:
        - uid: The unique identifier of the Sketchfab model (obtained from search_sketchfab_models)

        Returns the model's thumbnail as an Image for visual confirmation.
        """
        try:
            blender = self.connection
            logger.info(f"Getting Sketchfab model preview for UID: {uid}")

            result = blender.send_command(ActionName("get_sketchfab_model_preview"), {"uid": str(uid)})

            if result is None:
                raise ProviderError(ErrorMessage("Received no response from Blender"))

            if "error" in result:
                raise ProviderError(ErrorMessage(result["error"]))

            # Decode base64 image data
            image_data = base64.b64decode(result["image_data"])
            # Log model info
            model_name = result.get("model_name", "Unknown")
            author = result.get("author", "Unknown")
            logger.info(f"Preview retrieved for '{model_name}' by {author}")

            return ImageBytes(image_data)
        except ProviderError:
            raise
        except Exception as e:
            logger.error(f"Error getting Sketchfab preview: {str(e)}")
            raise Exception(f"Failed to get preview: {str(e)}") from e

    def download_sketchfab_model(self, uid: AssetId, target_size: ScaleFactor) -> StatusString:
        """
        Download and import a Sketchfab model by its UID.
        The model will be scaled so its largest dimension equals target_size.

        Parameters:
        - uid: The unique identifier of the Sketchfab model
        - target_size: REQUIRED. The target size in Blender units/meters for the largest dimension.
        You must specify the desired size for the model.

        Returns a message with import details including object names, dimensions, and bounding box.
        The model must be downloadable and you must have proper access rights.
        """
        try:
            blender = self.connection
            logger.info(f"Downloading Sketchfab model: {uid}, target_size={target_size}")

            result = blender.send_command(
                ActionName("download_sketchfab_model"),
                {
                    "uid": str(uid),
                    "normalize_size": True,  # Always normalize
                    "target_size": float(target_size),
                },
            )

            if result is None:
                logger.error("Received None result from Sketchfab download")
                return StatusString("Error: Received no response from Sketchfab download request")

            if "error" in result:
                logger.error(f"Error from Sketchfab download: {result['error']}")
                return StatusString(f"Error: {result['error']}")

            if result.get("success"):
                imported_objects = result.get("imported_objects", [])
                object_names = ", ".join(imported_objects) if imported_objects else "none"

                output = "Successfully imported model.\n"
                output += f"Created objects: {object_names}\n"

                # Add dimension info if available
                if result.get("dimensions"):
                    dims = result["dimensions"]
                    output += f"Dimensions (X, Y, Z): {dims[0]:.3f} x {dims[1]:.3f} x {dims[2]:.3f} meters\n"

                # Add bounding box info if available
                if result.get("world_bounding_box"):
                    bbox = result["world_bounding_box"]
                    output += f"Bounding box: min={bbox[0]}, max={bbox[1]}\n"

                # Add normalization info if applied
                if result.get("normalized"):
                    scale = result.get("scale_applied", 1.0)
                    output += f"Size normalized: scale factor {scale:.6f} applied (target size: {target_size}m)\n"

                return StatusString(output)
            else:
                return StatusString(f"Failed to download model: {result.get('message', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Error downloading Sketchfab model: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
            return StatusString(f"Error downloading Sketchfab model: {str(e)}")


# SketchfabApiClient is now purely a technical implementation that depends on a connection port.
# Module-level entry points have been moved to infrastructure/__init__.py or similar.
