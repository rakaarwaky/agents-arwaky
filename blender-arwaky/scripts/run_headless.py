"""
Unified Headless Engine for Blender MCP.
Combines robust path handling, multiple import strategies, and server state checking.
"""

import os
import sys
import time

print("\n=== Blender MCP Headless Engine (Unified) ===", flush=True)

# 1. Setup Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
src_dir = os.path.join(project_root, "src")

# Add paths to sys.path
for path in [src_dir, project_root]:
    if path not in sys.path:
        sys.path.insert(0, path)

# 2. Import bpy (Must be inside Blender)
try:
    import bpy  # type: ignore
except ImportError:
    print("[!] ERROR: bpy not found. This script must be run INSIDE Blender!", flush=True)
    sys.exit(1)

# 3. Load BlenderMCPServer Class (Multi-strategy)
BlenderMCPServer = None

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
except (ImportError, AttributeError) as e:
    print(f"[!] Primary import strategy failed: {e}", flush=True)
    # Strategy B: Direct path injection
    try:
        addon_pkg_path = os.path.join(project_root, "blender_mcp_addon")
        if addon_pkg_path not in sys.path:
            sys.path.append(addon_pkg_path)
        import server as server_mod  # type: ignore

        BlenderMCPServer = server_mod.BlenderMCPServer
        print("[+] Loaded BlenderMCPServer via direct path injection", flush=True)
    except ImportError as e2:
        print(f"[!] Fallback strategy failed: {e2}", flush=True)

if not BlenderMCPServer:
    print("[!] CRITICAL ERROR: Could not find BlenderMCPServer class!", flush=True)
    sys.exit(1)

# 4. Start or Re-use Server
port = 9876

# Check if server is already running in this Blender instance
if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server.running:
    print(f"[+] Server already running on port {bpy.types.blendermcp_server.port}", flush=True)
    server = bpy.types.blendermcp_server
else:
    print(f"[+] Starting server on port {port}...", flush=True)
    server = BlenderMCPServer(port=port)
    server.start()
    bpy.types.blendermcp_server = server  # type: ignore
    print(f"[+] Server started (running={server.running})", flush=True)

# 5. Main Loop
print("[+] Entering manual command loop — Press Ctrl+C to stop\n", flush=True)
try:
    while server.running:
        server.process_commands()
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n[+] Shutdown requested", flush=True)
finally:
    server.stop()
    print("[+] Server stopped — goodbye!", flush=True)
