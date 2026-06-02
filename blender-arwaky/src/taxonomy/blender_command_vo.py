"""
Taxonomy: Command Catalog — Action dispatch definitions.

This module defines the canonical COMMAND_CATALOG that maps MCP action names
to capability contracts (protocol.method). Both handlers and capabilities
import from here — handlers to list/validate actions, capabilities to resolve.

AES Compliance:
- Pure data, no business logic
- No imports from higher layers (agent/capabilities/infrastructure)
- Handlers and capabilities depend on this taxonomy module only.
"""

from typing import Any

# CommandSpec describes a single command entry
CommandSpec = dict[str, Any]  # TypedDict would be better but keep simple for now


# The canonical command catalog
class CommandCatalog:
    """Canonical command catalog mapping action names to capability contracts."""

    COMMAND_CATALOG: dict[str, CommandSpec] = {
        # ──────────────────────────────────────────────────────────────
        # Scene Domain (SceneOperateProtocol)
        # ──────────────────────────────────────────────────────────────
        "get_scene_info": {
            "description": "Get detailed information about the current Blender scene",
            "capability": "SceneOperateProtocol.get_scene_info",
            "parameters": {},
            "domain": "scene",
            "returns": "GetSceneInfoResponseIO",
        },
        "cleanup_scene": {
            "description": "Remove all objects from the current scene",
            "capability": "SceneOperateProtocol.cleanup_scene",
            "parameters": {"mode": "Cleanup mode: 'all', 'objects', 'meshes'"},
            "domain": "scene",
            "returns": "CleanupSceneResponseIO",
        },
        "setup_environment": {
            "description": "Setup scene environment (HDRI, lighting)",
            "capability": "SceneOperateProtocol.setup_environment",
            "parameters": {
                "hdri_id": "HDR image identifier from polyhaven",
                "strength": "Environment light strength",
            },
            "domain": "scene",
            "returns": "SetupEnvironmentResponseIO",
        },
        # ──────────────────────────────────────────────────────────────
        # Object Domain (ObjectOperateProtocol)
        # ──────────────────────────────────────────────────────────────
        "get_object_info": {
            "description": "Get detailed information about a specific object",
            "capability": "ObjectOperateProtocol.get_object_info",
            "parameters": {"object_name": "The name of the object"},
            "domain": "object",
            "returns": "GetObjectInfoResponseIO",
        },
        "place_asset": {
            "description": "Place an imported asset into the scene",
            "capability": "ObjectOperateProtocol.place_asset",
            "parameters": {
                "asset_id": "Asset identifier",
                "location": "[x, y, z] coordinates",
                "rotation": "[x, y, z] Euler angles",
                "scale": "[x, y, z] scale factors",
            },
            "domain": "object",
            "returns": "PlaceAssetResponseIO",
        },
        "set_object_transform": {
            "description": "Update transform of an existing object",
            "capability": "ObjectOperateProtocol.set_object_transform",
            "parameters": {
                "object_name": "Name of target object",
                "location": "Optional [x, y, z]",
                "rotation": "Optional [x, y, z]",
                "scale": "Optional [x, y, z]",
            },
            "domain": "object",
            "returns": "SetObjectTransformResponseIO",
        },
        "delete_object": {
            "description": "Delete object from scene",
            "capability": "ObjectOperateProtocol.delete_object",
            "parameters": {"object_name": "Name of object to delete"},
            "domain": "object",
            "returns": "DeleteObjectResponseIO",
        },
        "create_primitive": {
            "description": "Create a basic 3D primitive (Cube, Sphere, etc.)",
            "capability": "ObjectOperateProtocol.create_primitive",
            "parameters": {
                "primitive_type": "Type of primitive: CUBE, SPHERE, PLANE, etc.",
                "location": "Optional location",
                "scale": "Optional scale",
            },
            "domain": "object",
            "returns": "CreatePrimitiveResponseIO",
        },
        "set_material": {
            "description": "Assign a material to an object",
            "capability": "ObjectOperateProtocol.set_material",
            "parameters": {
                "object_name": "Target object name",
                "material_name": "Name of material to assign",
            },
            "domain": "object",
            "returns": "SetMaterialResponseIO",
        },
        "apply_modifier": {
            "description": "Apply a modifier to an object",
            "capability": "ObjectOperateProtocol.apply_modifier",
            "parameters": {
                "object_name": "Target object name",
                "modifier_name": "Name of modifier (SUBSURF, BEVEL, etc.)",
            },
            "domain": "object",
            "returns": "ApplyModifierResponseIO",
        },
        # ──────────────────────────────────────────────────────────────
        # Render & Viewport Domain (RenderOperateProtocol)
        # ──────────────────────────────────────────────────────────────
        "get_viewport_screenshot": {
            "description": "Capture a screenshot of the current Blender 3D viewport",
            "capability": "RenderOperateProtocol.get_viewport_screenshot",
            "parameters": {"max_size": "Maximum size in pixels (default: 800)"},
            "domain": "viewport",
            "returns": "ScreenshotResponseIO",
        },
        "render": {
            "description": "Execute full frame render to file",
            "capability": "RenderOperateProtocol.render",
            "parameters": {
                "output_path": "Path to save the rendered image",
                "resolution_x": "Width in pixels",
                "resolution_y": "Height in pixels",
            },
            "domain": "render",
            "returns": "RenderResponseIO",
        },
        # ──────────────────────────────────────────────────────────────
        # Import/Export Domain (ImportExportProtocol)
        # ──────────────────────────────────────────────────────────────
        "import_glb": {
            "description": "Import a GLB/GLTF model",
            "capability": "ImportExportProtocol.import_glb",
            "parameters": {"file_path": "Absolute path to GLB file"},
            "domain": "io",
            "returns": "ImportGlbResponseIO",
        },
        "export_model": {
            "description": "Export model to file",
            "capability": "ImportExportProtocol.export_model",
            "parameters": {
                "object_name": "Name of object to export",
                "file_path": "Target file path",
                "export_format": "glb, obj, etc.",
            },
            "domain": "io",
            "returns": "ExportModelResponseIO",
        },
        # ──────────────────────────────────────────────────────────────
        # Code Execution (Infrastructure)
        # ──────────────────────────────────────────────────────────────
        "execute_blender_code": {
            "description": "Execute arbitrary Python code in Blender",
            "capability": "BlenderPort.execute_code",
            "parameters": {"code": "The Python code to execute"},
            "domain": "infrastructure",
            "returns": "Execution output string",
        },
        # ──────────────────────────────────────────────────────────────
        # Asset Search & Generation (ProviderPort)
        # ──────────────────────────────────────────────────────────────
        "search_all_assets": {
            "description": "Search for assets across providers",
            "capability": "AssetProviderPort.search_assets",
            "parameters": {"query": "Search string"},
            "domain": "asset",
            "returns": "AssetSearchResponseIO",
        },
        "start_generation": {
            "description": "Start AI 3D generation",
            "capability": "GenerationProviderPort.start_generation",
            "parameters": {"prompt": "Description"},
            "domain": "generation",
            "returns": "GenerationStartResponseIO",
        },
        "poll_generation": {
            "description": "Poll generation job status",
            "capability": "GenerationProviderPort.poll_generation",
            "parameters": {"job_id": "Job ID"},
            "domain": "generation",
            "returns": "GenerationStatusResponseIO",
        },
    }

    @staticmethod
    def list_actions() -> list[str]:
        """Return all available action names."""
        return list(CommandCatalog.COMMAND_CATALOG.keys())


# Module-level aliases for backward compatibility
COMMAND_CATALOG = CommandCatalog.COMMAND_CATALOG
list_actions = CommandCatalog.list_actions
