"""Handler: MCP server instance lifecycle (FastMCP).

Responsibilities:
- Create FastMCP instance with configuration
- Manage startup/shutdown lifecycle (lifespan context manager)
- Initialize/teardown resources via telemetry service
- Wire DI container and agent system
- Expose `mcp` instance for registration by server_runner

AES Compliance (Handler Layer):
- Imports from: agent, contract, taxonomy (allowed)
- NO direct imports from capabilities or infrastructure
- Delegates all logic to AgentOrchestrator
"""

import logging
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from agent.system_utils_coordinator import (
    get_blender_connection,
    record_startup,
    shutdown_connection,
)
from contract import ServerBootstrapManagerAggregate
from taxonomy import Details, ServerName

logger = logging.getLogger("BlenderMCPServer")

# Lazy singleton: set to None on import, created on first access
_mcp_instance = None
_mcp_lock = threading.Lock()


class ServerInstanceHandler:
    """Handler for MCP server instance lifecycle management."""

    _contract_ref: ServerBootstrapManagerAggregate

    @staticmethod
    @asynccontextmanager
    async def server_lifespan(_server: FastMCP) -> AsyncIterator[Details]:
        """
        Manage server startup and shutdown lifecycle.

        During startup:
        1. Record telemetry_service (best effort)
        2. Verify Blender connection (non-fatal)
        3. Initialize agent orchestrator (lazy)
        """
        logger.info("BlenderMCP server starting up")

        startup_data: Details = {}

        try:
            # Record startup telemetry (non-blocking)
            record_startup()

            # Defer Blender connection probe. Doing it inline during lifespan
            # makes the MCP server susceptible to Hermes marking it unhealthy if
            # Blender is not yet running. Connection will be established later
            # on the first actual tool call.
            logger.info(
                "BlenderMCP server is up; Blender connection deferred until first tool call"
            )
            startup_data["blender_connected"] = False

            yield startup_data

        except BaseException as e:
            logger.error(f"Startup error: {e}")
            yield {"blender_connected": False, "startup_error": str(e)}
        finally:
                logger.info("BlenderMCP server shut down")

    @staticmethod
    def get_mcp_instance(name: ServerName | None = None) -> FastMCP:
        name = name or ServerName("BlenderMCP")
        """Return the singleton MCP instance, creating it lazily on first call.

        Args:
            name: Server name displayed in MCP clients

        Returns:
            Configured FastMCP instance with lifespan and instructions
        """
        global _mcp_instance
        with _mcp_lock:
            if _mcp_instance is not None:
                return _mcp_instance

            _mcp_instance = FastMCP(
                name=name,
                instructions="Blender MCP Server — 3D asset search, AI generation, scene assembly via standardized tool pipelines.",
                lifespan=ServerInstanceHandler.server_lifespan,
            )

            # Register tools and prompts (Handler layer delegation)
            from .prompt_register_handler import register_prompts
            from .tool_registry_handler import register_tools

            register_tools(_mcp_instance)
            register_prompts(_mcp_instance)

            return _mcp_instance
