#!/usr/bin/env python3
"""
BlenderMCP CLI — Unlimited command dispatcher.

Usage:
  blender-mcp <action> [--args JSON]

All actions are defined in COMMAND_CATALOG (src.surfaces.catalog_command_handler).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent.agent_di_container import AgentDiContainer

from contract import AgentDiContainerAggregate, CoreAgentOrchestratorAggregate
from taxonomy import Details, ExitCode, Prompt

# ── Path setup ────────────────────────────────────────────────────────────────
_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

logger = logging.getLogger("blender-mcp-cli_entry_point")


class CliCommandHandler:
    """Handler for CLI help command."""

    _contract_ref: AgentDiContainerAggregate

    _orchestrator: CoreAgentOrchestratorAggregate | None = None

    @classmethod
    def _get_container(cls) -> AgentDiContainer:
        """Get DI container (not capabilities directly — AES compliant)."""
        from agent.agent_di_container import get_container

        container = get_container()
        if container is None:
            raise RuntimeError("DI container not initialized — call start_server first")
        return container

    @classmethod
    def get_orchestrator(cls) -> CoreAgentOrchestratorAggregate:
        """Lazy-load CoreAgentOrchestrator from DI container."""
        if cls._orchestrator is None:
            container = cls._get_container()
            cls._orchestrator = container.core_agent_orchestrator
        return cls._orchestrator

    @classmethod
    def build_action_map(cls) -> Details:
        """
        Build action map using DI container aggregate execute_action.
        All actions dispatch through the DI container.
        """
        container = cls._get_container()
        from taxonomy.blender_command_vo import CommandCatalog

        action_map: Details = {}

        for action_name in CommandCatalog.COMMAND_CATALOG:

            async def action_wrapper(
                an=action_name,
                cont=container,
                **kwargs: Any,
            ) -> Prompt:
                from taxonomy import ActionName

                orchestrator = cont.core_agent_orchestrator
                result = await orchestrator.execute_action(ActionName(an), kwargs)
                return Prompt(str(result))

            action_map[action_name] = action_wrapper

        return action_map

    @classmethod
    def main(cls) -> ExitCode:
        """Main CLI entry point."""
        from taxonomy.blender_command_vo import CommandCatalog as CommandCat

        parser = argparse.ArgumentParser(description="BlenderMCP CLI — unlimited actions via AgentOrchestrator")
        parser.add_argument("action", choices=sorted(CommandCat.COMMAND_CATALOG.keys()), help="Action to execute")
        parser.add_argument("--args", type=str, default="{}", help="JSON string of arguments (default: {})")
        parser.add_argument("--json-output", action="store_true", help="Force JSON output (default when not TTY)")
        parser.add_argument(
            "--log-level", default="WARNING", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging level"
        )

        opts = parser.parse_args()

        logging.basicConfig(
            level=getattr(logging, opts.log_level), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        try:
            args: Details = json.loads(opts.args)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing --args: {e}")
            return ExitCode(1)

        action_map = cls.build_action_map()
        if opts.action not in action_map:
            logger.error(f"Action '{opts.action}' not found in action map")
            return ExitCode(1)

        func = action_map[opts.action]

        try:
            result = asyncio.run(func(**args))
        except Exception as e:
            logger.error(f"Action '{opts.action}' failed: {e}", exc_info=True)
            logger.error(f"Error: {e}")
            return ExitCode(1)

        if opts.json_output or not sys.stdout.isatty():
            from pydantic import BaseModel

            if isinstance(result, BaseModel):
                print(result.model_dump_json(indent=2))
            else:
                print(json.dumps(result, indent=2, default=str))
        else:
            if isinstance(result, str):
                print(result)
            else:
                print(json.dumps(result, indent=2, default=str))

        return ExitCode(0)


# Module-level alias for backward compatibility
main = CliCommandHandler.main
