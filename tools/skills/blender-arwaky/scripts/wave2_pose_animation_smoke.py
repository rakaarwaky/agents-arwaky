from __future__ import annotations

import sys
from pathlib import Path

import bpy

sys.path.insert(0, "/home/ubuntu/blender-arwaky")

from blender_mcp_addon.server import BlenderMCPServer


EVIDENCE_BLEND = Path("/home/ubuntu/mpfb_native_rigify_evidence/native_mpfb2_rigify_character.blend")

bpy.ops.wm.open_mainfile(filepath=str(EVIDENCE_BLEND))
server = BlenderMCPServer()
armature = next(
    (obj for obj in bpy.data.objects if obj.type == "ARMATURE" and len(obj.data.bones) >= 500),
    None,
)
if armature is None:
    raise RuntimeError("Native Rigify control armature was not found in evidence scene")

pose_bone = armature.pose.bones.get("upper_arm_ik.L")
if pose_bone is None:
    raise RuntimeError("Expected Rigify IK control was not found")

server._activate_pose_armature(armature.name)
pose_bone.rotation_mode = "XYZ"
pose_bone.rotation_euler[2] = 0.35
bpy.ops.pose.select_all(action="SELECT")

create_response = server.execute_command(
    {
        "type": "create_pose_asset",
        "params": {"armature_name": armature.name, "pose_name": "Wave2_Left_Arm_Pose"},
    }
)
if create_response.get("status") != "success":
    raise RuntimeError(f"Pose asset creation failed: {create_response}")
asset_name = create_response["result"]["name"]
if not create_response["result"].get("is_pose_asset"):
    raise RuntimeError(f"Created Action is not marked as pose asset: {create_response}")

list_response = server.execute_command(
    {"type": "list_pose_assets", "params": {"limit": 100}}
)
if list_response.get("status") != "success":
    raise RuntimeError(f"Pose asset listing failed: {list_response}")
if not any(item.get("name") == asset_name for item in list_response["result"].get("assets", [])):
    raise RuntimeError("Created pose asset was not returned by list_pose_assets")

apply_response = server.execute_command(
    {
        "type": "apply_pose_asset",
        "params": {
            "armature_name": armature.name,
            "asset_name": asset_name,
            "blend_factor": 1.0,
            "flipped": True,
        },
    }
)
if apply_response.get("status") != "success":
    raise RuntimeError(f"Flipped pose asset application failed: {apply_response}")
if not apply_response["result"].get("flipped"):
    raise RuntimeError(f"Flipped application result was not marked mirrored: {apply_response}")

print(
    "WAVE2_POSE_ANIMATION_LIVE_OK",
    {
        "blender_version": bpy.app.version_string,
        "armature_name": armature.name,
        "rigify_bone_count": len(armature.data.bones),
        "asset_name": asset_name,
        "pose_asset_count": list_response["result"].get("count"),
        "flipped_asset_applied": apply_response["result"].get("flipped"),
    },
)
