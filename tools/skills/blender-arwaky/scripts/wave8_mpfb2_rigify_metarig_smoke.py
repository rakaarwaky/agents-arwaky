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
character.name = "Wave8_MPFB2_Character"

server = BlenderMCPServer()
params = {
    "character_object_name": character.name,
    "armature_name": "Wave8_Rigify_Control",
    "preset": "human",
    "bind_character": True,
    "replace_existing": False,
}
first_response = server.execute_command({"type": "create_rigify_metarig", "params": params})
if first_response.get("status") != "success":
    raise RuntimeError(f"First metarig workflow failed: {first_response}")
first = first_response["result"]

second_response = server.execute_command({"type": "create_rigify_metarig", "params": params})
if second_response.get("status") != "success":
    raise RuntimeError(f"Idempotent metarig workflow failed: {second_response}")
second = second_response["result"]

armature = bpy.data.objects.get("Wave8_Rigify_Control")
if armature is None or armature.type != "ARMATURE":
    raise RuntimeError("Native workflow did not create a generated Rigify armature")
if armature.show_in_front is not True:
    raise RuntimeError("Final Rigify armature is not configured to show in front")
if getattr(armature.data, "display_type", None) != "OCTAHEDRAL":
    raise RuntimeError("Final Rigify armature display type is not OCTAHEDRAL")
if len(armature.data.bones) < 500:
    raise RuntimeError("Native generated Rigify rig has unexpectedly few bones")
modifiers = [item for item in character.modifiers if item.type == "ARMATURE"]
if len(modifiers) < 2 or any(item.object != armature for item in modifiers):
    raise RuntimeError("Native MPFB2 armature modifiers are not bound to the generated Rigify rig")
if first["created"] is not True or second["created"] is not False:
    raise RuntimeError(f"Native Rigify workflow is not idempotent: first={first}, second={second}")
if second["bound"] is not True:
    raise RuntimeError(f"Native binding result is invalid: {second}")
if first.get("native_rig") != "rigify.human_toes" or first.get("native_loaded") is not True:
    raise RuntimeError(f"Native MPFB2 Rigify data was not used: {first}")
if first.get("metarig_bone_count", 0) < 200 or first.get("deform_bone_count", 0) < 100:
    raise RuntimeError(f"Native Rigify rig definition or generated DEF bones are incomplete: {first}")

print(
    "WAVE8_MPFB2_RIGIFY_NATIVE_WORKFLOW_LIVE_OK",
    {
        "blender_version": bpy.app.version_string,
        "character_name": character.name,
        "armature_name": armature.name,
        "show_in_front": armature.show_in_front,
        "display_type": getattr(armature.data, "display_type", None),
        "bone_count": len(armature.data.bones),
        "deform_bone_count": len([bone for bone in armature.data.bones if bone.use_deform]),
        "armature_modifiers": [(item.name, item.object.name if item.object else None) for item in modifiers],
        "native_rig": first["native_rig"],
        "metarig_bone_count": first["metarig_bone_count"],
        "first_created": first["created"],
        "second_created": second["created"],
        "second_bound": second["bound"],
    },
)
