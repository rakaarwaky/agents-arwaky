"""Blender 5.2 live smoke test for MPFB2 randomize/remove lifecycle."""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
BlenderMCPServer = importlib.import_module("blender_mcp_addon.server").BlenderMCPServer

import bpy  # noqa: E402


def run(server: BlenderMCPServer, action: str, params: dict) -> dict:
    response = server.execute_command({"type": action, "params": params})
    assert response["status"] == "success", (action, response)  # nosec B101
    result = response["result"]
    assert isinstance(result, dict), (action, result)  # nosec B101
    return result


def mesh_digest(object_name: str) -> str:
    obj = bpy.data.objects[object_name]
    payload = ";".join(",".join(f"{value:.9f}" for value in vertex.co) for vertex in obj.data.vertices)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


bpy.ops.wm.read_factory_settings(use_empty=True)
server = BlenderMCPServer()
unrelated = run(server, "create_primitive", {"primitive_type": "CUBE", "name": "Wave4Unrelated"})
assert unrelated["name"] == "Wave4Unrelated"  # nosec B101

first = run(
    server,
    "randomize_character",
    {"plugin_id": "mpfb2", "name": "Wave4CharacterA", "seed": 424242},
)
first_digest = mesh_digest(first["object_name"])
second = run(
    server,
    "randomize_character",
    {"plugin_id": "mpfb2", "name": "Wave4CharacterB", "seed": 424242},
)
second_digest = mesh_digest(second["object_name"])
assert first["seed"] == second["seed"] == 424242  # nosec B101
assert first["object_name"] == "Wave4CharacterA"  # nosec B101
assert second["object_name"] == "Wave4CharacterB"  # nosec B101
assert first_digest == second_digest, (first_digest, second_digest)  # nosec B101

removed = run(
    server,
    "remove_character",
    {"plugin_id": "mpfb2", "object_name": "Wave4CharacterA", "confirm": True},
)
assert "Wave4CharacterA" in removed["removed_objects"]  # nosec B101
assert bpy.data.objects.get("Wave4CharacterA") is None  # nosec B101
assert bpy.data.objects.get("Wave4CharacterB") is not None  # nosec B101
assert bpy.data.objects.get("Wave4Unrelated") is not None  # nosec B101

invalid = server.execute_command(
    {
        "type": "remove_character",
        "params": {"plugin_id": "mpfb2", "object_name": "Wave4CharacterB", "confirm": False},
    }
)
assert invalid["status"] == "error"  # nosec B101

print("WAVE4_MPFB2_RANDOM_REMOVE_SMOKE_OK")
print(json.dumps({"first": first, "second": second, "removed": removed}))
