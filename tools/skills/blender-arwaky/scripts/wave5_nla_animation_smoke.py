from __future__ import annotations

import sys
from pathlib import Path

import bpy

sys.path.insert(0, "/home/ubuntu/blender-arwaky")

from blender_mcp_addon.server import BlenderMCPServer


EVIDENCE_BLEND = Path("/home/ubuntu/mpfb_native_rigify_evidence/native_mpfb2_rigify_character.blend")

bpy.ops.wm.open_mainfile(filepath=str(EVIDENCE_BLEND))
server = BlenderMCPServer()
target = next(
    (obj for obj in bpy.data.objects if obj.type == "ARMATURE" and len(obj.data.bones) >= 500),
    None,
)
if target is None:
    raise RuntimeError("Native Rigify target armature was not found")

def make_action(name: str, bone_name: str, frame_values: tuple[tuple[int, float], ...]):
    action = bpy.data.actions.new(name)
    target.animation_data_create()
    target.animation_data.action = action
    bone = target.pose.bones.get(bone_name)
    if bone is None:
        raise RuntimeError(f"Rigify test control not found: {bone_name}")
    bone.rotation_mode = "XYZ"
    for frame, value in frame_values:
        bpy.context.scene.frame_set(frame)
        bone.rotation_euler[1] = value
        bone.keyframe_insert(data_path="rotation_euler", frame=frame)
    return action

walk_action = make_action("Wave5_Walk_Action", "upper_arm_parent.L", ((1, 0.0), (12, 0.25), (24, 0.0)))
gesture_action = make_action("Wave5_Gesture_Action", "hand_ik.L", ((1, 0.0), (12, -0.4), (24, 0.0)))
target.animation_data.action = None


def execute(command: str, params: dict):
    response = server.execute_command({"type": command, "params": params})
    if response.get("status") != "success":
        raise RuntimeError(f"{command} failed: {response}")
    return response["result"]

base_track = execute("create_nla_track", {"armature_name": target.name, "track_name": "Base Motion"})
upper_track = execute("create_nla_track", {"armature_name": target.name, "track_name": "Upper Body"})
walk_strip = execute(
    "add_nla_strip",
    {
        "armature_name": target.name,
        "track_name": "Base Motion",
        "action_name": walk_action.name,
        "strip_name": "Walk Strip",
        "frame_start": 1,
        "blend_in": 2,
        "blend_out": 2,
        "influence": 1.0,
    },
)
gesture_strip = execute(
    "add_nla_strip",
    {
        "armature_name": target.name,
        "track_name": "Upper Body",
        "action_name": gesture_action.name,
        "strip_name": "Gesture Strip",
        "frame_start": 1,
        "blend_type": "ADD",
        "influence": 0.8,
    },
)
layer = execute(
    "set_animation_layer",
    {"armature_name": target.name, "track_name": "Upper Body", "blend_type": "ADD", "influence": 0.5},
)
mask = execute(
    "set_animation_mask",
    {"armature_name": target.name, "track_name": "Upper Body", "strip_name": "Gesture Strip", "bone_names": ["hand_ik.L"]},
)
updated_strip = execute(
    "set_nla_strip",
    {"armature_name": target.name, "track_name": "Base Motion", "strip_name": "Walk Strip", "frame_start": 3, "scale": 1.0, "influence": 0.9},
)
validation_before_remove = execute("validate_nla_assembly", {"armature_name": target.name, "limit": 100})
if not validation_before_remove.get("approved") or validation_before_remove.get("strip_count") != 2:
    raise RuntimeError(f"Unexpected NLA validation: {validation_before_remove}")
removed = execute("remove_nla_strip", {"armature_name": target.name, "track_name": "Upper Body", "strip_name": "Gesture Strip"})
if not removed.get("removed"):
    raise RuntimeError(f"NLA strip removal failed: {removed}")
execute(
    "add_nla_strip",
    {
        "armature_name": target.name,
        "track_name": "Upper Body",
        "action_name": gesture_action.name,
        "strip_name": "Gesture Strip Final",
        "frame_start": 1,
        "blend_type": "ADD",
        "influence": 0.5,
    },
)
final_validation = execute("validate_nla_assembly", {"armature_name": target.name, "limit": 100})
if not final_validation.get("approved") or final_validation.get("strip_count") != 2:
    raise RuntimeError(f"Unexpected final NLA validation: {final_validation}")
bake = execute(
    "bake_nla_assembly",
    {
        "armature_name": target.name,
        "frame_start": 1,
        "frame_end": 24,
        "step": 1,
        "output_action": "Wave5_Final_Assembly_Action",
        "clear_constraints": False,
        "clear_nla": True,
    },
)
if bake.get("output_action") != "Wave5_Final_Assembly_Action" or bake.get("keyframe_count", 0) <= 0:
    raise RuntimeError(f"NLA bake failed: {bake}")

print(
    "WAVE5_NLA_ANIMATION_LIVE_OK",
    {
        "blender_version": bpy.app.version_string,
        "target_armature": target.name,
        "target_bone_count": len(target.data.bones),
        "base_track": base_track,
        "upper_track": upper_track,
        "walk_strip": walk_strip,
        "gesture_strip": gesture_strip,
        "layer": layer,
        "mask": mask,
        "updated_strip": updated_strip,
        "validation_before_remove": validation_before_remove,
        "removed": removed,
        "final_validation": final_validation,
        "bake": bake,
    },
)
