from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import bpy

sys.path.insert(0, "/home/ubuntu/blender-arwaky")

from blender_mcp_addon.server import BlenderMCPServer


EVIDENCE_BLEND = Path("/home/ubuntu/mpfb_native_rigify_evidence/native_mpfb2_rigify_character.blend")
TEST_DIR = Path(tempfile.mkdtemp(prefix="arwaky-wave1-"))
BVH_PATH = TEST_DIR / "arwaky_wave1_test_motion.bvh"


bpy.ops.wm.open_mainfile(filepath=str(EVIDENCE_BLEND))
server = BlenderMCPServer()

armature = next(
    (obj for obj in bpy.data.objects if obj.type == "ARMATURE" and len(obj.data.bones) >= 500),
    None,
)
if armature is None:
    raise RuntimeError("Native Rigify control armature was not found in evidence scene")

action = bpy.data.actions.get("Wave1_Native_Imported_Action") or bpy.data.actions.new("Wave1_Native_Imported_Action")

link_response = server.execute_command(
    {
        "type": "link_action_to_armature",
        "params": {"armature_name": armature.name, "action_name": action.name},
    }
)
if link_response.get("status") != "success":
    raise RuntimeError(f"Action linking failed: {link_response}")

pose_bone = next((bone for bone in armature.pose.bones if not bone.bone.use_deform), None)
if pose_bone is None:
    raise RuntimeError("An animator pose bone was not found")
pose_bone.rotation_mode = "XYZ"
bpy.context.scene.frame_set(1)
pose_bone.rotation_euler[2] = 0.0
pose_bone.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
bpy.context.scene.frame_set(24)
pose_bone.rotation_euler[2] = 0.35
pose_bone.keyframe_insert(data_path="rotation_euler", index=2, frame=24)

list_response = server.execute_command(
    {"type": "list_animation_actions", "params": {"armature_name": armature.name, "limit": 100}}
)
if list_response.get("status") != "success":
    raise RuntimeError(f"Action listing failed: {list_response}")
if not any(item.get("name") == action.name for item in list_response["result"].get("actions", [])):
    raise RuntimeError("Linked native Action was not returned by list_animation_actions")

BVH_PATH.write_text(
    """HIERARCHY\nROOT Hips\n{\n OFFSET 0 0 0\n CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation\n End Site\n {\n  OFFSET 0 1 0\n }\n}\nMOTION\nFrames: 2\nFrame Time: 0.0333333\n0 0 0 0 0 0\n0 0 0 0 0 0\n""",
    encoding="utf-8",
)
import_response = server.execute_command(
    {"type": "import_animation_file", "params": {"source_path": str(BVH_PATH), "importer": "bvh"}}
)
if import_response.get("status") != "success":
    raise RuntimeError(f"Native BVH import failed: {import_response}")
if import_response["result"].get("importer") != "bvh":
    raise RuntimeError(f"Unexpected importer result: {import_response}")

invalid_response = server.execute_command(
    {"type": "import_animation_file", "params": {"source_path": str(TEST_DIR / "unsupported.glb")}}
)
if invalid_response.get("status") != "error":
    raise RuntimeError(f"Unsupported importer was not rejected: {invalid_response}")

print(
    "WAVE1_NATIVE_ANIMATION_LIVE_OK",
    {
        "blender_version": bpy.app.version_string,
        "armature_name": armature.name,
        "bone_count": len(armature.data.bones),
        "linked_action": link_response["result"]["action_name"],
        "listed_action_count": list_response["result"].get("count"),
        "imported_objects": import_response["result"].get("imported_objects"),
        "imported_actions": import_response["result"].get("action_names"),
        "invalid_import_rejected": invalid_response.get("status") == "error",
    },
)
