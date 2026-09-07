import math
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, "/home/ubuntu/blender-arwaky")
from blender_mcp_addon.server import BlenderMCPServer
from bl_ext.user_default.mpfb.services.humanservice import HumanService


def evaluated_points(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    evaluated.to_mesh_clear()
    return points


def max_displacement(first, second):
    return max((a - b).length for a, b in zip(first, second))


bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.preferences.addon_enable(module="rigify")
character = HumanService.create_human()
if character is None or character.type != "MESH":
    raise RuntimeError("MPFB2 did not create a character mesh")
character.name = "Native_Deformation_MPFB2_Character"

server = BlenderMCPServer()
response = server.execute_command(
    {
        "type": "create_rigify_metarig",
        "params": {
            "character_object_name": character.name,
            "armature_name": "Native_Deformation_Rigify_Control",
            "preset": "human",
            "bind_character": True,
            "replace_existing": False,
        },
    }
)
if response.get("status") != "success":
    raise RuntimeError(response)
rig = bpy.data.objects.get("Native_Deformation_Rigify_Control")
if rig is None:
    raise RuntimeError("Native Rigify control rig missing")

bpy.context.view_layer.update()
rest_points = evaluated_points(character)
pose_bone = rig.pose.bones.get("upper_arm_ik.L")
if pose_bone is None:
    raise RuntimeError("Rigify upper_arm_ik.L control missing")
pose_response = server.execute_command(
    {
        "type": "set_pose_bone_transform",
        "params": {
            "armature_name": rig.name,
            "bone_name": pose_bone.name,
            "rotation_euler": [math.radians(-42.0), math.radians(18.0), math.radians(-24.0)],
        },
    }
)
if pose_response.get("status") != "success":
    raise RuntimeError(f"Canonical pose action failed: {pose_response}")
hand_bone = rig.pose.bones.get("hand_ik.L")
if hand_bone is not None:
    hand_response = server.execute_command(
        {
            "type": "set_pose_bone_transform",
            "params": {
                "armature_name": rig.name,
                "bone_name": hand_bone.name,
                "rotation_euler": [math.radians(10.0), math.radians(-12.0), math.radians(18.0)],
            },
        }
    )
    if hand_response.get("status") != "success":
        raise RuntimeError(f"Canonical hand pose action failed: {hand_response}")
bpy.context.view_layer.update()
posed_points = evaluated_points(character)
posed_displacement = max_displacement(rest_points, posed_points)
changed_vertices = sum(1 for first, second in zip(rest_points, posed_points) if (first - second).length > 1e-5)
if posed_displacement <= 0.01 or changed_vertices <= 100:
    raise RuntimeError(
        f"Native Rigify pose did not deform the mesh sufficiently: displacement={posed_displacement}, changed={changed_vertices}"
    )

for bone_name in (pose_bone.name, hand_bone.name if hand_bone is not None else None):
    if bone_name is None:
        continue
    reset_response = server.execute_command(
        {
            "type": "set_pose_bone_transform",
            "params": {
                "armature_name": rig.name,
                "bone_name": bone_name,
                "location": [0.0, 0.0, 0.0],
                "rotation_euler": [0.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0],
            },
        }
    )
    if reset_response.get("status") != "success":
        raise RuntimeError(f"Canonical pose reset failed: {reset_response}")
bpy.context.view_layer.update()
reset_points = evaluated_points(character)
reset_displacement = max_displacement(rest_points, reset_points)
if reset_displacement > 0.002:
    raise RuntimeError(f"Native Rigify pose reset did not restore rest state: displacement={reset_displacement}")

print(
    "NATIVE_MPFB2_RIGIFY_DEFORMATION_OK",
    {
        "blender_version": bpy.app.version_string,
        "character": character.name,
        "rig": rig.name,
        "bone_count": len(rig.data.bones),
        "deform_bone_count": len([bone for bone in rig.data.bones if bone.use_deform]),
        "pose_control": pose_bone.name,
        "posed_max_displacement": round(posed_displacement, 6),
        "changed_vertices": changed_vertices,
        "reset_max_displacement": round(reset_displacement, 6),
    },
)
