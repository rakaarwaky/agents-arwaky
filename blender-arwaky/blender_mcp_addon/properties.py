import logging
import os

import bpy  # type: ignore
from bpy.props import (  # type: ignore
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    StringProperty,
)

from .config import get_config

logger = logging.getLogger(__name__)


def register_properties():
    bpy.types.Scene.blendermcp_port = IntProperty(
        name="Port",
        description="Port for the BlenderMCP server",
        default=get_config("blender.port", 9876),
        min=1024,
        max=65535,
    )

    bpy.types.Scene.blendermcp_server_running = BoolProperty(name="Server Running", default=False)

    bpy.types.Scene.blendermcp_use_polyhaven = BoolProperty(
        name="Use Poly Haven",
        description="Enable Poly Haven asset integration",
        default=False,
    )

    bpy.types.Scene.blendermcp_use_hyper3d = BoolProperty(
        name="Use Hyper3D Rodin",
        description="Enable Hyper3D Rodin generation integration",
        default=False,
    )

    bpy.types.Scene.blendermcp_hyper3d_mode = EnumProperty(
        name="Rodin Mode",
        description="Choose the platform used to call Rodin APIs",
        items=[
            ("MAIN_SITE", "hyper3d.ai", "hyper3d.ai"),
            ("FAL_AI", "fal.ai", "fal.ai"),
        ],
        default="MAIN_SITE",
    )

    bpy.types.Scene.blendermcp_hyper3d_api_key = StringProperty(
        name="Hyper3D API Key",
        subtype="PASSWORD",
        description="API Key provided by Hyper3D",
        default="",
    )

    bpy.types.Scene.blendermcp_use_hunyuan3d = BoolProperty(
        name="Use Hunyuan 3D",
        description="Enable Hunyuan asset integration",
        default=False,
    )

    bpy.types.Scene.blendermcp_hunyuan3d_mode = EnumProperty(
        name="Hunyuan3D Mode",
        description="Choose a local or official APIs",
        items=[
            ("LOCAL_API", "local api", "local api"),
            ("OFFICIAL_API", "official api", "official api"),
        ],
        default="LOCAL_API",
    )

    bpy.types.Scene.blendermcp_hunyuan3d_secret_id = StringProperty(
        name="Hunyuan 3D SecretId",
        description="SecretId provided by Hunyuan 3D",
        default="",
    )

    bpy.types.Scene.blendermcp_hunyuan3d_secret_key = StringProperty(
        name="Hunyuan 3D SecretKey",
        subtype="PASSWORD",
        description="SecretKey provided by Hunyuan 3D",
        default="",
    )

    bpy.types.Scene.blendermcp_hunyuan3d_api_url = StringProperty(
        name="API URL",
        description="URL of the Hunyuan 3D API service",
        default=get_config("hunyuan.api_url", "http://localhost:8081"),
    )

    bpy.types.Scene.blendermcp_hunyuan3d_octree_resolution = IntProperty(
        name="Octree Resolution",
        description="Octree resolution for the 3D generation",
        default=256,
        min=128,
        max=512,
    )

    bpy.types.Scene.blendermcp_hunyuan3d_num_inference_steps = IntProperty(
        name="Number of Inference Steps",
        description="Number of inference steps for the 3D generation",
        default=20,
        min=20,
        max=50,
    )

    bpy.types.Scene.blendermcp_hunyuan3d_guidance_scale = FloatProperty(
        name="Guidance Scale",
        description="Guidance scale for the 3D generation",
        default=5.5,
        min=1.0,
        max=10.0,
    )

    bpy.types.Scene.blendermcp_hunyuan3d_texture = BoolProperty(
        name="Generate Texture",
        description="Whether to generate texture for the 3D model",
        default=False,
    )

    bpy.types.Scene.blendermcp_use_sketchfab = BoolProperty(
        name="Use Sketchfab",
        description="Enable Sketchfab asset integration",
        default=False,
    )

    bpy.types.Scene.blendermcp_sketchfab_api_key = StringProperty(
        name="Sketchfab API Key",
        subtype="PASSWORD",
        description="API Key provided by Sketchfab",
        default="",
    )


def unregister_properties():
    del bpy.types.Scene.blendermcp_port
    del bpy.types.Scene.blendermcp_server_running
    del bpy.types.Scene.blendermcp_use_polyhaven
    del bpy.types.Scene.blendermcp_use_hyper3d
    del bpy.types.Scene.blendermcp_hyper3d_mode
    del bpy.types.Scene.blendermcp_hyper3d_api_key
    del bpy.types.Scene.blendermcp_use_sketchfab
    del bpy.types.Scene.blendermcp_sketchfab_api_key
    del bpy.types.Scene.blendermcp_use_hunyuan3d
    del bpy.types.Scene.blendermcp_hunyuan3d_mode
    del bpy.types.Scene.blendermcp_hunyuan3d_secret_id
    del bpy.types.Scene.blendermcp_hunyuan3d_secret_key
    del bpy.types.Scene.blendermcp_hunyuan3d_api_url
    del bpy.types.Scene.blendermcp_hunyuan3d_octree_resolution
    del bpy.types.Scene.blendermcp_hunyuan3d_num_inference_steps
    del bpy.types.Scene.blendermcp_hunyuan3d_guidance_scale
    del bpy.types.Scene.blendermcp_hunyuan3d_texture


def register():
    register_properties()


def unregister():
    unregister_properties()


def inject_env_vars(scene):
    if not scene:
        return
    env_mappings = {
        "blendermcp_sketchfab_api_key": "BLENDERMCP_SKETCHFAB_API_KEY",
        "blendermcp_hyper3d_api_key": "BLENDERMCP_HYPER3D_API_KEY",
        "blendermcp_hunyuan3d_secret_id": "BLENDERMCP_HUNYUAN3D_SECRET_ID",
        "blendermcp_hunyuan3d_secret_key": "BLENDERMCP_HUNYUAN3D_SECRET_KEY",
        "blendermcp_hunyuan3d_api_url": "BLENDERMCP_HUNYUAN3D_API_URL",
    }
    for scene_prop, env_var in env_mappings.items():
        if not getattr(scene, scene_prop, ""):
            val = os.getenv(env_var)
            if val:
                setattr(scene, scene_prop, val)
                logger.info("Injected %s from env var %s", scene_prop, env_var)
