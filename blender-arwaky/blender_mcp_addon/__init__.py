"""
Blender MCP Addon
==================
Blender-side plugin that runs a TCP server to receive commands from
an external MCP server (Claude, etc.) and execute them in Blender.

Install:   Edit -> Preferences -> Add-ons -> Install -> select this folder
Register:  Enable "Interface: Blender MCP"
"""

bl_info = {
    "name": "Blender MCP Addon",
    "author": "BlenderMCPAddon",
    "description": "Connect Blender to Claude (or any MCP client)",
    "version": (1, 6, 2),
    "blender": (3, 0, 0),
    "location": "View3D -> Sidebar -> BlenderMCP",
    "category": "Interface",
}

import logging  # noqa: E402

import bpy  # type: ignore[import-untyped]  # noqa: E402 -- bl_info first for Blender addon convention

logger = logging.getLogger("blender-mcp-addon")

# -- Persistent auto-start ------------------------------------------------
_AUTO_START_RETRIES = 30  # max attempts
_AUTO_START_INTERVAL = 2.0  # seconds between attempts
_auto_start_attempt = 0
_auto_start_timer = None


def _auto_start() -> float | None:
    """Persistent auto-start: retries every 2s until server is running.

    Returns None (stop) on success, or float (continue) on retry.
    """
    global _auto_start_attempt, _auto_start_timer

    from . import properties
    from .server import BlenderMCPServer

    _auto_start_attempt += 1

    scn = bpy.context.scene if hasattr(bpy.context, "scene") else None
    if scn is None:
        logger.info(
            "BlenderMCP: no scene yet (attempt %d/%d)",
            _auto_start_attempt,
            _AUTO_START_RETRIES,
        )
        if _auto_start_attempt >= _AUTO_START_RETRIES:
            logger.warning(
                "BlenderMCP: gave up auto-start (no scene after %d attempts)",
                _AUTO_START_RETRIES,
            )
            _auto_start_timer = None
            return None
        return _AUTO_START_INTERVAL

    try:
        properties.inject_env_vars(scn)

        if not hasattr(bpy.types, "blendermcp_server") or not bpy.types.blendermcp_server:
            bpy.types.blendermcp_server = BlenderMCPServer(port=scn.blendermcp_port)

        if not bpy.types.blendermcp_server.running:
            bpy.types.blendermcp_server.start()
            scn.blendermcp_server_running = True

        logger.info("BlenderMCP server auto-started on port %s", scn.blendermcp_port)
        _auto_start_attempt = 0
        _auto_start_timer = None
        return None  # stop timer -- success

    except Exception as exc:  # pragma: no cover
        logger.error(  # pragma: no cover
            "BlenderMCP auto-start attempt %d failed: %s",
            _auto_start_attempt,
            exc,
        )
        if _auto_start_attempt >= _AUTO_START_RETRIES:  # pragma: no cover
            logger.warning(  # pragma: no cover
                "BlenderMCP: gave up auto-start after %d attempts",
                _AUTO_START_RETRIES,
            )
            _auto_start_timer = None  # pragma: no cover
            return None  # pragma: no cover
        return _AUTO_START_INTERVAL  # pragma: no cover


def register() -> None:
    from . import (
        operators,
        properties,
        ui,
    )

    properties.register_properties()
    operators.register()
    ui.register()

    # -- Inject env vars into current scene -----------------------------
    scene = bpy.context.scene if hasattr(bpy.context, "scene") and bpy.context.scene else None
    if scene:
        properties.inject_env_vars(scene)

    # -- Persistent auto-start server -----------------------------------
    global _auto_start_timer
    _auto_start_timer = bpy.app.timers.register(
        _auto_start,
        first_interval=1.0,
        persistent=True,
    )
    logger.info("BlenderMCP addon registered (auto-start enabled)")


def unregister() -> None:
    # Stop auto-start timer
    global _auto_start_timer
    if _auto_start_timer is not None:
        try:
            bpy.app.timers.unregister(_auto_start)
        except Exception as e:  # pragma: no cover
            logger.debug("Error unregistering auto-start timer: %s", e)
        _auto_start_timer = None

    # Stop server
    if hasattr(bpy.types, "blendermcp_server") and bpy.types.blendermcp_server:
        try:
            bpy.types.blendermcp_server.stop()
        except Exception as e:  # pragma: no cover
            logger.debug("Error stopping server: %s", e)
        del bpy.types.blendermcp_server

    from . import operators, properties, ui

    operators.unregister()
    ui.unregister()
    properties.unregister_properties()

    logger.info("BlenderMCP addon unregistered")


if __name__ == "__main__":  # pragma: no cover
    register()  # pragma: no cover
