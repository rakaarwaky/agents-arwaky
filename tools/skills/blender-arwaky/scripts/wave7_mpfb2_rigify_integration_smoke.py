import sys

import bpy

sys.path.insert(0, "/home/ubuntu/blender-arwaky")

from blender_mcp_addon.server import BlenderMCPServer


bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.preferences.addon_enable(module="rigify")

try:
    from bl_ext.user_default.mpfb.services.humanservice import HumanService
except ImportError as error:
    raise RuntimeError("MPFB2 HumanService is unavailable") from error

objects_before = set(bpy.data.objects)
character = HumanService.create_human()
if character is None:
    active = bpy.context.view_layer.objects.active
    character = active if active not in objects_before else None
if character is None:
    raise RuntimeError("MPFB2 did not create a character object")

new_meshes = [obj for obj in bpy.data.objects if obj not in objects_before and obj.type == "MESH"]
if character.type != "MESH":
    character = new_meshes[0] if new_meshes else None
if character is None or character.type != "MESH":
    raise RuntimeError("MPFB2 character did not produce a mesh object")
character.name = "Wave7_MPFB2_Character"

bpy.ops.object.armature_human_metarig_add()
armature = bpy.context.object
armature.name = "Wave7_Rigify_Metarig"

server = BlenderMCPServer()
response = server.execute_command(
    {
        "type": "bind_character_to_rig",
        "params": {
            "character_object_name": character.name,
            "armature_name": armature.name,
            "modifier_name": "Wave7_Rigify_Armature",
            "replace_existing": False,
        },
    }
)
if response.get("status") != "success":
    raise RuntimeError(f"Binding command failed: {response}")
result = response["result"]

modifier = character.modifiers.get("Wave7_Rigify_Armature")
if modifier is None or modifier.type != "ARMATURE":
    raise RuntimeError("Binding did not create the expected armature modifier")
if modifier.object != armature:
    raise RuntimeError("Binding modifier does not reference the Rigify metarig")
if result["operation"] != "bind_character_to_rig":
    raise RuntimeError(f"Unexpected binding operation: {result}")

print(
    "WAVE7_MPFB2_RIGIFY_LIVE_OK",
    {
        "blender_version": bpy.app.version_string,
        "character_name": character.name,
        "character_type": character.type,
        "armature_name": armature.name,
        "modifier_name": modifier.name,
        "modifier_target": modifier.object.name,
        "replaced_count": result["replaced_count"],
    },
)
