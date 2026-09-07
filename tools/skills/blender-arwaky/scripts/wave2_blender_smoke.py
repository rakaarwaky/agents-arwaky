"""Blender background smoke test for Wave 2 core capabilities."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
BlenderMCPServer = importlib.import_module("blender_mcp_addon.server").BlenderMCPServer


server = BlenderMCPServer()


def run(action: str, params: dict | None = None) -> dict:
    response = server.execute_command({"type": action, "params": params or {}})
    assert response["status"] == "success", (action, response)  # nosec B101
    result = response["result"]
    assert isinstance(result, dict), (action, result)  # nosec B101
    return result


created = run("create_primitive", {"primitive_type": "CUBE", "name": "Wave2Cube"})
assert created["name"] == "Wave2Cube"  # nosec B101

group_result = run(
    "create_geometry_node_group",
    {"node_group_name": "Wave2Geometry", "object_name": "Wave2Cube"},
)
assert group_result["group_name"] == "Wave2Geometry"  # nosec B101
assert group_result["modifier_name"]  # nosec B101

inspected = run("inspect_geometry_node_group", {"node_group_name": "Wave2Geometry"})
assert inspected["node_count"] == 2  # nosec B101
assert inspected["link_count"] == 1  # nosec B101

run("set_timeline_range", {"frame_start": 1, "frame_end": 24, "current_frame": 1})
keyframe = run(
    "insert_object_keyframe",
    {"object_name": "Wave2Cube", "frame": 1, "data_path": "location"},
)
assert keyframe["frame"] == 1  # nosec B101
animation = run("get_animation_state", {"object_name": "Wave2Cube"})
assert animation["curve_count"] >= 1  # nosec B101

statistics = run("get_mesh_statistics", {"object_name": "Wave2Cube"})
assert statistics["vertex_count"] == 8  # nosec B101
validation = run("validate_mesh", {"object_name": "Wave2Cube"})
assert validation["valid"] is True  # nosec B101
uv_result = run("ensure_mesh_uv_layer", {"object_name": "Wave2Cube", "uv_layer_name": "Wave2UV"})
assert uv_result["uv_layer_name"] == "Wave2UV"  # nosec B101
normal_result = run(
    "perform_mesh_edit_operation",
    {"object_name": "Wave2Cube", "operation": "recalculate_normals"},
)
assert normal_result["operation"] == "recalculate_normals"  # nosec B101

invalid = server.execute_command(
    {"type": "insert_object_keyframe", "params": {"object_name": "Wave2Cube", "frame": 1, "data_path": "location.x"}}
)
assert invalid["status"] == "error"  # nosec B101

print("WAVE2_SMOKE_OK")
print(json.dumps({"geometry": inspected, "animation": animation, "mesh": statistics}))
