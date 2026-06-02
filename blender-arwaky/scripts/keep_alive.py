#!/usr/bin/env python3
"""
Lightweight keep-alive script for Blender MCP.
Ensures the server remains running in background mode.
"""

import os
import sys
import time

print("\n=== Blender MCP Keep-Alive (v2) ===", flush=True)

# 1. Setup Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
src_dir = os.path.join(project_root, "src")

# Add paths to sys.path
for path in [src_dir, project_root]:
    if path not in sys.path:
        sys.path.insert(0, path)

# 2. Import bpy
try:
    import bpy  # type: ignore
except ImportError:
    print("[!] ERROR: bpy not found. This script must be run INSIDE Blender!", flush=True)
    sys.exit(1)

# Strategy A: Try importing as 'blender_mcp_addon'
try:
    import blender_mcp_addon as addon_pkg  # type: ignore

    # Only register if not already enabled to prevent crashes/duplicates
    addon_name = addon_pkg.bl_info.get("name", "Blender MCP")

    # Check if enabled with safety checks for mypy
    pref = bpy.context.preferences
    is_enabled = False
    if pref and hasattr(pref, "addons"):
        is_enabled = addon_name in pref.addons or "blender_mcp_addon" in pref.addons  # type: ignore

    if not is_enabled:
        print("[+] Addon not detected in preferences, registering manually...", flush=True)
        addon_pkg.register()
    else:
        print("[+] Addon already enabled in Blender, skipping manual registration", flush=True)

    BlenderMCPServer = addon_pkg.server.BlenderMCPServer
    print("[+] Loaded BlenderMCPServer class", flush=True)
except ImportError:
    # Try direct path injection as fallback
    addon_pkg_path = os.path.join(project_root, "blender_mcp_addon")
    if addon_pkg_path not in sys.path:
        sys.path.append(addon_pkg_path)
    try:
        import server as server_mod  # type: ignore

        BlenderMCPServer = server_mod.BlenderMCPServer
        print("[+] Loaded BlenderMCPServer via fallback path", flush=True)
    except ImportError as e:
        print(f"[!] CRITICAL: Could not find server module: {e}", flush=True)
        sys.exit(1)

if not BlenderMCPServer:
    print("[!] CRITICAL ERROR: Could not find BlenderMCPServer class!", flush=True)
    sys.exit(1)

# 4. Start Server
port = 9876
server = BlenderMCPServer(port=port)
server.start()
bpy.types.blendermcp_server = server  # type: ignore
print(f"[+] Server started on port {port}", flush=True)

# 5. Main Loop (Manual pumping for background mode)
print("[+] Processing commands... Press Ctrl+C to stop\n", flush=True)
try:
    while server.running:
        server.process_commands()
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n[+] Shutdown requested", flush=True)
finally:
    server.stop()
    print("[+] Server stopped", flush=True)
