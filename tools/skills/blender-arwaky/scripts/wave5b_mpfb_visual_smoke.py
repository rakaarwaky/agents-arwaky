"""Blender 5.2 visual smoke test for an MPFB2-generated character."""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
BlenderMCPServer = importlib.import_module("blender_mcp_addon.server").BlenderMCPServer


OUTPUT_DIR = Path(__file__).resolve().parents[1] / "artifacts"
OUTPUT_PATH = OUTPUT_DIR / "wave5b_mpfb2_character.png"
BLEND_PATH = OUTPUT_DIR / "wave5b_mpfb2_character.blend"


def run(server: BlenderMCPServer, action: str, params: dict[str, object]) -> dict[str, object]:
    response = server.execute_command({"type": action, "params": params})
    if response.get("status") != "success":
        raise RuntimeError(f"{action} failed: {response}")
    result = response.get("result")
    if not isinstance(result, dict):
        raise RuntimeError(f"{action} returned invalid result: {result!r}")
    return result


def world_bounds(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    if not points:
        raise RuntimeError("MPFB2 character has no renderable bound box")
    minimum = Vector((min(point.x for point in points), min(point.y for point in points), min(point.z for point in points)))
    maximum = Vector((max(point.x for point in points), max(point.y for point in points), max(point.z for point in points)))
    return minimum, maximum


def point_camera(camera: bpy.types.Object, target: Vector) -> None:
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()


def create_scene(character_name: str) -> dict[str, object]:
    character = bpy.data.objects.get(character_name)
    if character is None:
        raise RuntimeError(f"character object {character_name!r} not found")
    character_objects = [
        obj
        for obj in bpy.context.scene.objects
        if obj is character or obj.parent is character or obj.name.startswith(f"{character_name}.")
    ]
    minimum, maximum = world_bounds(character_objects)
    center = (minimum + maximum) * 0.5
    height = max(maximum.z - minimum.z, 1.0)

    bpy.ops.mesh.primitive_plane_add(size=max(height * 4.0, 4.0), location=(center.x, center.y, minimum.z))
    floor = bpy.context.object
    floor.name = "Wave5BRenderFloor"

    floor_material = bpy.data.materials.new("Wave5BFloorMaterial")
    floor_material.diffuse_color = (0.055, 0.065, 0.085, 1.0)
    floor.data.materials.append(floor_material)

    camera_data = bpy.data.cameras.new("Wave5BRenderCamera")
    camera = bpy.data.objects.new("Wave5BRenderCamera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (center.x, center.y - height * 2.4, center.z + height * 0.12)
    camera_data.lens = 58
    point_camera(camera, center + Vector((0.0, 0.0, height * 0.05)))
    bpy.context.scene.camera = camera

    light_data = bpy.data.lights.new("Wave5BKeyLight", type="AREA")
    light_data.energy = 1100
    light_data.shape = "DISK"
    light_data.size = height * 1.2
    key_light = bpy.data.objects.new("Wave5BKeyLight", light_data)
    bpy.context.collection.objects.link(key_light)
    key_light.location = (center.x - height * 0.9, center.y - height * 1.3, center.z + height * 1.5)
    point_camera(key_light, center)

    fill_data = bpy.data.lights.new("Wave5BFillLight", type="AREA")
    fill_data.energy = 500
    fill_data.size = height
    fill_light = bpy.data.objects.new("Wave5BFillLight", fill_data)
    bpy.context.collection.objects.link(fill_light)
    fill_light.location = (center.x + height * 1.1, center.y - height * 0.5, center.z + height * 0.7)
    point_camera(fill_light, center)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 640
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUTPUT_PATH)
    scene.render.film_transparent = False
    if scene.world is None:
        scene.world = bpy.data.worlds.new("Wave5BRenderWorld")
    scene.world.color = (0.012, 0.018, 0.03)
    scene.render.filepath = str(OUTPUT_PATH)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.ops.render.render(write_still=True)
    return {
        "character_name": character_name,
        "character_objects": [obj.name for obj in character_objects],
        "bounds": {"min": list(minimum), "max": list(maximum)},
        "render_path": str(OUTPUT_PATH),
        "blend_path": str(BLEND_PATH),
    }


bpy.ops.wm.read_factory_settings(use_empty=True)
server = BlenderMCPServer()
asset_archive = Path("/home/ubuntu/blender-arwaky/.cache/mpfb2/makehuman_system_assets_cc0.zip")
asset_digest = hashlib.sha256(asset_archive.read_bytes()).hexdigest()
installed = run(
    server,
    "install_mpfb_asset_pack",
    {
        "plugin_id": "mpfb2",
        "asset_pack_id": "makehuman_system_assets",
        "cache_path": str(asset_archive),
        "sha256": asset_digest,
    },
)
asset_status = run(server, "inspect_mpfb_assets", {"plugin_id": "mpfb2"})
assert asset_status["system_assets_installed"] is True  # nosec B101
from bl_ext.user_default.mpfb.services.assetservice import AssetService
from bl_ext.user_default.mpfb.services.humanservice import HumanService

skin_assets = AssetService.list_mhmat_assets()
if not skin_assets:
    raise RuntimeError("MPFB2 system asset pack installed without any skin assets")
result = run(server, "randomize_character", {"plugin_id": "mpfb2", "name": "Wave5BVisualCharacter", "seed": 20260816})
character = bpy.data.objects[str(result["object_name"])]
HumanService.set_character_skin(str(skin_assets[0]), character)
visual = create_scene(str(result["object_name"]))
print("WAVE5B_MPFB2_VISUAL_SMOKE_OK")
print(json.dumps({"installed": installed, "asset_status": asset_status, "operation": result, "skin": str(skin_assets[0]), "visual": visual}, default=str))
