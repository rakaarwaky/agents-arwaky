import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, "/home/ubuntu/blender-arwaky")
from bl_ext.user_default.mpfb.services.humanservice import HumanService

from blender_mcp_addon.server import BlenderMCPServer

OUTPUT_DIR = Path("/home/ubuntu/mpfb_native_rigify_evidence")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
BEAUTY_PATH = OUTPUT_DIR / "native_mpfb2_rigify_character.png"
BLEND_PATH = OUTPUT_DIR / "native_mpfb2_rigify_character.blend"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def frame_character(character, camera):
    points = [character.matrix_world @ Vector(corner) for corner in character.bound_box]
    minimum = Vector((min(point.x for point in points), min(point.y for point in points), min(point.z for point in points)))
    maximum = Vector((max(point.x for point in points), max(point.y for point in points), max(point.z for point in points)))
    center = (minimum + maximum) / 2.0
    height = max(maximum.z - minimum.z, 1.0)
    camera.location = center + Vector((height * 0.72, -height * 2.35, height * 0.12))
    camera.data.lens = 58
    look_at(camera, center + Vector((0.0, 0.0, height * 0.03)))


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.preferences.addon_enable(module="rigify")
    character = HumanService.create_human()
    if character is None or character.type != "MESH":
        raise RuntimeError("MPFB2 did not create a mesh character")
    character.name = "Native_Render_MPFB2_Character"

    server = BlenderMCPServer()
    response = server.execute_command(
        {
            "type": "create_rigify_metarig",
            "params": {
                "character_object_name": character.name,
                "armature_name": "Native_Render_Rigify_Control",
                "preset": "human",
                "bind_character": True,
                "replace_existing": False,
            },
        }
    )
    if response.get("status") != "success":
        raise RuntimeError(response)
    result = response["result"]
    rig = bpy.data.objects.get("Native_Render_Rigify_Control")
    if rig is None or rig.type != "ARMATURE":
        raise RuntimeError("Native final Rigify rig was not created")

    pose = rig.pose.bones.get("upper_arm_ik.L")
    if pose is None:
        raise RuntimeError("Generated Rigify control bone upper_arm_ik.L is unavailable")
    pose.rotation_mode = "XYZ"
    pose.rotation_euler = (math.radians(-26.0), math.radians(12.0), math.radians(-14.0))
    hand = rig.pose.bones.get("hand_ik.L")
    if hand is not None:
        hand.rotation_mode = "XYZ"
        hand.rotation_euler = (math.radians(8.0), math.radians(-10.0), math.radians(14.0))

    bpy.ops.object.camera_add(location=(0.0, -4.0, 1.2))
    camera = bpy.context.object
    camera.name = "Native_Render_Camera"
    frame_character(character, camera)
    bpy.context.scene.camera = camera

    for light_type, location, energy, size, name in (
        ("AREA", (2.5, -3.5, 4.5), 950, 3.0, "Native_Render_Key"),
        ("AREA", (-3.0, -1.0, 2.5), 450, 3.5, "Native_Render_Fill"),
        ("AREA", (0.5, 2.5, 4.0), 700, 2.5, "Native_Render_Rim"),
    ):
        bpy.ops.object.light_add(type=light_type, location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        look_at(light, character.location)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 700
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(BEAUTY_PATH)
    scene.world.color = (0.015, 0.02, 0.035)
    for object_item in scene.objects:
        if object_item.type == "ARMATURE":
            object_item.hide_render = True
    rig.show_in_front = True
    rig.hide_viewport = False
    rig.data.display_type = "OCTAHEDRAL"
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig

    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.ops.render.render(write_still=True)
    modifiers = [item for item in character.modifiers if item.type == "ARMATURE"]
    print(
        "NATIVE_MPFB2_RIGIFY_RENDER_OK",
        {
            "image": str(BEAUTY_PATH),
            "blend": str(BLEND_PATH),
            "character": character.name,
            "rig": rig.name,
            "bone_count": len(rig.data.bones),
            "deform_bone_count": len([bone for bone in rig.data.bones if bone.use_deform]),
            "native_rig": result.get("native_rig"),
            "modifiers": [(item.name, item.object.name if item.object else None) for item in modifiers],
            "pose_bone": pose.name,
        },
    )


main()
