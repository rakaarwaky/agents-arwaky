"""Blender background smoke test for Wave 4 advanced simulation controls."""

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


run("create_primitive", {"primitive_type": "CUBE", "name": "Wave4Cube"})
particle = run(
    "configure_particle_system",
    {
        "object_name": "Wave4Cube",
        "enabled": True,
        "count": 100,
        "frame_start": 1,
        "frame_end": 60,
        "lifetime": 20.0,
        "physics_type": "NEWTON",
    },
)
assert particle["particle_system_name"]  # nosec B101

force = run(
    "configure_force_field",
    {"object_name": "Wave4Cube", "enabled": True, "field_type": "WIND", "strength": 10.0, "noise": 0.5},
)
assert force["force_field_type"] == "WIND"  # nosec B101

fluid = run(
    "configure_fluid_domain",
    {
        "object_name": "Wave4Cube",
        "enabled": True,
        "domain_type": "LIQUID",
        "resolution": 32,
        "cache_type": "REPLAY",
    },
)
assert fluid["fluid_domain_type"] == "LIQUID"  # nosec B101

state = run("get_simulation_state", {"object_name": "Wave4Cube"})
assert state["particle_systems"]  # nosec B101
assert state["force_field_type"] == "WIND"  # nosec B101
assert state["fluid_domain_type"] == "LIQUID"  # nosec B101

cache = run("get_simulation_cache_status")
assert cache["frame_end"] >= cache["frame_start"]  # nosec B101
assert any(item["object_name"] == "Wave4Cube" for item in cache["cache_states"])  # nosec B101

run("configure_fluid_domain", {"object_name": "Wave4Cube", "enabled": False})
run("configure_force_field", {"object_name": "Wave4Cube", "enabled": False})
run("configure_particle_system", {"object_name": "Wave4Cube", "enabled": False})

invalid = server.execute_command(
    {
        "type": "configure_particle_system",
        "params": {"object_name": "Wave4Cube", "enabled": True, "count": 1_000_001},
    }
)
assert invalid["status"] == "error"  # nosec B101

print("WAVE4_SMOKE_OK")
print(json.dumps({"particle": particle, "force": force, "fluid": fluid, "cache": cache}))
