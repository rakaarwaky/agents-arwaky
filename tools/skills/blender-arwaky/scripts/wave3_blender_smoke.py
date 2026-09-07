"""Blender background smoke test for Wave 3 core capabilities."""

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


run("configure_compositor", {"use_nodes": True})
rgb = run("create_compositor_node", {"node_type": "CompositorNodeRGB", "node_name": "Wave3RGB"})
composite = run(
    "create_compositor_node",
    {"node_type": "CompositorNodeComposite", "node_name": "Wave3Composite"},
)
assert rgb["node_name"] == "Wave3RGB"  # nosec B101
assert composite["node_name"] == "Wave3Composite"  # nosec B101
initial_compositor = run("inspect_compositor_nodes", {"limit": 100})
rgb_node = next(node for node in initial_compositor["nodes"] if node["name"] == "Wave3RGB")
composite_node = next(node for node in initial_compositor["nodes"] if node["name"] == "Wave3Composite")
run(
    "set_compositor_link",
    {
        "from_node": "Wave3RGB",
        "from_socket": rgb_node["outputs"][0],
        "to_node": "Wave3Composite",
        "to_socket": composite_node["inputs"][0],
    },
)
compositor = run("inspect_compositor_nodes", {"limit": 100})
assert any(node["name"] == "Wave3RGB" for node in compositor["nodes"])  # nosec B101
assert any(link["from_node"] == "Wave3RGB" for link in compositor["links"])  # nosec B101

created_strip = run(
    "create_sequence_strip",
    {"strip_type": "COLOR", "strip_name": "Wave3Color", "channel": 1, "frame_start": 1, "frame_end": 24},
)
assert created_strip["strip_name"] == "Wave3Color"  # nosec B101
sequence = run("inspect_sequence_editor", {"limit": 100})
assert sequence["sequence_present"] is True  # nosec B101
assert sequence["strips"][0]["name"] == "Wave3Color"  # nosec B101
run("remove_sequence_strip", {"strip_name": "Wave3Color"})
assert run("inspect_sequence_editor", {"limit": 100})["strips"] == []  # nosec B101

run("create_primitive", {"primitive_type": "CUBE", "name": "Wave3Cube"})
rigid = run(
    "configure_rigid_body",
    {"object_name": "Wave3Cube", "enabled": True, "body_type": "ACTIVE", "mass": 2.0},
)
cloth = run(
    "configure_cloth_simulation",
    {"object_name": "Wave3Cube", "enabled": True, "quality": 3},
)
assert rigid["body_type"] == "ACTIVE"  # nosec B101
assert cloth["quality"] == 3  # nosec B101
physics = run("get_physics_state", {"object_name": "Wave3Cube"})
assert physics["rigid_body_enabled"] is True  # nosec B101
assert physics["cloth_enabled"] is True  # nosec B101
run("configure_cloth_simulation", {"object_name": "Wave3Cube", "enabled": False})
run("configure_rigid_body", {"object_name": "Wave3Cube", "enabled": False})

invalid = server.execute_command(
    {
        "type": "create_sequence_strip",
        "params": {"strip_type": "MOVIE", "strip_name": "Missing", "channel": 1, "frame_start": 1},
    }
)
assert invalid["status"] == "error"  # nosec B101

print("WAVE3_SMOKE_OK")
print(json.dumps({"compositor": compositor, "sequence": sequence, "physics": physics}))
