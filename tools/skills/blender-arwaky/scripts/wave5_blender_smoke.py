"""Blender background smoke test for Wave 5 rigging and deformation."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
BlenderMCPServer = importlib.import_module("blender_mcp_addon.server").BlenderMCPServer


server = BlenderMCPServer()


def run(action: str, params: dict | None = None) -> dict:
    response = server.execute_command({"type": action, "params": params or {}})
    assert response["status"] == "success", (action, response)  # nosec B101
    result = response["result"]
    assert isinstance(result, dict), (action, result)  # nosec B101
    return result


armature_data = bpy.data.armatures.new("Wave5RigData")
armature = bpy.data.objects.new("Wave5Rig", armature_data)
bpy.context.scene.collection.objects.link(armature)
bpy.context.view_layer.objects.active = armature
armature.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
root = armature_data.edit_bones.new("Root")
root.head = (0.0, 0.0, 0.0)
root.tail = (0.0, 0.0, 1.0)
child = armature_data.edit_bones.new("Child")
child.head = (0.0, 0.0, 1.0)
child.tail = (0.0, 0.0, 2.0)
child.parent = root
bpy.ops.object.mode_set(mode="OBJECT")
armature.select_set(False)

target = bpy.data.objects.new("Wave5Target", None)
bpy.context.scene.collection.objects.link(target)

run("create_primitive", {"primitive_type": "CUBE", "name": "Wave5Mesh"})
mesh = bpy.data.objects["Wave5Mesh"]
armature_modifier = mesh.modifiers.new(name="Wave5Armature", type="ARMATURE")
armature_modifier.object = armature

armature_state = run("inspect_armature", {"object_name": "Wave5Rig", "limit": 10})
assert armature_state["bone_count"] == 2  # nosec B101
assert armature_state["bones"][1]["parent"] == "Root"  # nosec B101

pose = run(
    "set_pose_bone_transform",
    {"armature_name": "Wave5Rig", "bone_name": "Child", "rotation_euler": [0.0, 0.0, 0.5]},
)
assert pose["bone_name"] == "Child"  # nosec B101

constraint = run(
    "configure_bone_constraint",
    {
        "armature_name": "Wave5Rig",
        "bone_name": "Child",
        "constraint_type": "COPY_ROTATION",
        "enabled": True,
        "constraint_name": "Wave5CopyRotation",
        "target_object": "Wave5Target",
    },
)
assert constraint["constraint_name"] == "Wave5CopyRotation"  # nosec B101

shape_key = run(
    "configure_shape_key",
    {
        "object_name": "Wave5Mesh",
        "shape_key_name": "Smile",
        "enabled": True,
        "value": 0.5,
        "slider_min": 0.0,
        "slider_max": 1.0,
    },
)
assert shape_key["shape_key_name"] == "Smile"  # nosec B101

deformation = run("get_deformation_state", {"object_name": "Wave5Mesh"})
assert deformation["armature_modifiers"][0]["object_name"] == "Wave5Rig"  # nosec B101
assert any(item["name"] == "Wave5CopyRotation" for item in deformation["constraints"])  # nosec B101
assert any(item["name"] == "Smile" for item in deformation["shape_keys"])  # nosec B101

run(
    "configure_bone_constraint",
    {
        "armature_name": "Wave5Rig",
        "bone_name": "Child",
        "constraint_type": "COPY_ROTATION",
        "enabled": False,
        "constraint_name": "Wave5CopyRotation",
    },
)
run(
    "configure_shape_key",
    {"object_name": "Wave5Mesh", "shape_key_name": "Smile", "enabled": False},
)

invalid = server.execute_command(
    {
        "type": "set_pose_bone_transform",
        "params": {"armature_name": "Wave5Rig", "bone_name": "Child", "location": [0.0, 0.0]},
    }
)
assert invalid["status"] == "error"  # nosec B101

print("WAVE5_SMOKE_OK")
print(json.dumps({"armature": armature_state, "deformation": deformation}))
