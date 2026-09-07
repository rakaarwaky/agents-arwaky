"""Live Blender 5.2 smoke test for the MPFB2 system asset lifecycle."""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
BlenderMCPServer = importlib.import_module("blender_mcp_addon.server").BlenderMCPServer


def run(server: BlenderMCPServer, action: str, params: dict[str, object]) -> dict[str, object]:
    response = server.execute_command({"type": action, "params": params})
    assert response["status"] == "success", (action, response)  # nosec B101
    result = response["result"]
    assert isinstance(result, dict), (action, result)  # nosec B101
    return result


bpy.ops.wm.read_factory_settings(use_empty=True)
server = BlenderMCPServer()
archive = Path("/home/ubuntu/blender-arwaky/.cache/mpfb2/makehuman_system_assets_cc0.zip")
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
installed = run(
    server,
    "install_mpfb_asset_pack",
    {
        "plugin_id": "mpfb2",
        "asset_pack_id": "makehuman_system_assets",
        "cache_path": str(archive),
        "sha256": digest,
    },
)
inspection = run(server, "inspect_mpfb_assets", {"plugin_id": "mpfb2"})
assert inspection["system_assets_installed"] is True  # nosec B101
assert "makehuman_system_assets" in inspection["pack_names"]  # nosec B101
created = run(
    server,
    "create_character",
    {"plugin_id": "mpfb2", "name": "Wave5BTexturedCharacter"},
)
assert created["object_name"] == "Wave5BTexturedCharacter"  # nosec B101
print("WAVE5B_MPFB_ASSET_SMOKE_OK")
print(json.dumps({"installed": installed, "inspection": inspection, "created": created}))
