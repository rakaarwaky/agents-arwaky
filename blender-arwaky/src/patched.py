import textwrap, pathlib

p = pathlib.Path('/home/raka/mcp-servers/blender-mcp/src/surfaces/server_instance_handler.py')
text = p.read_text()

old = '''        try:
            # Record startup telemetry (best-effort)
            record_startup()

            # Verify Blender connection (non-fatal). We keep it here but run it
            # through a thread so it never blocks the asyncio lifespan shutdown.
            try:
                conn = get_blender_connection()
                if conn:
                    logger.info("✓ Blender connection verified")
                    startup_data["blender_connected"] = True
                else:
                    logger.warning("⚠ Blender not available — will retry on first tool call")
                    startup_data["blender_connected"] = False
            except Exception as e:
                logger.warning(f"⚠ Blender connection check failed: {e}")
                startup_data["blender_connected"] = False

            # AgentOrchestrator lazy-init on first interaction
            yield startup_data

        except Exception as e:
            logger.error(f"Startup error: {e}")
            yield {"blender_connected": False, "startup_error": str(e)}
'''

new = '''        try:
            # Record startup telemetry (best-effort)
            record_startup()

            # Skip blocking Blender connectivity probe during MCP server
            # startup. Hermes may use stdio-only healthchecks, and a slow
            # TCP connect can make the server look unhealthy "out of the gate".
            # Connection is established lazily on the first tool call.
            logger.info(
                "BlenderMCP server is up; Blender connection deferred until first tool call"
            )
            startup_data["blender_connected"] = False

            yield startup_data

        except Exception as e:
            logger.error(f"Startup error: {e}")
            yield {"blender_connected": False, "startup_error": str(e)}
'''

if old in text:
    text = text.replace(old, new)
    p.write_text(text)
    print('patched server_instance_handler.py')
else:
    print('expected block not found, no patch applied')
