"""
Dispatcher: Route MCP actions to AgentOrchestrator.

This capability is the sole entry point for executing any BlenderMCP action.
Handlers (MCP tools, CLI) delegate here — they contain no business logic.
"""

import logging
import re
from typing import Any

from contract import ExecuteActionProtocol
from taxonomy import ActionName, Details, Prompt
from taxonomy.blender_command_vo import CommandCatalog, CommandSpec

logger = logging.getLogger("BlenderMCPServer")

# Validation constants
MAX_ACTION_NAME_LENGTH = 100
MAX_STRING_ARG_LENGTH = 50_000
ACTION_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class ActionExecuteActions(ExecuteActionProtocol):
    """Dispatches actions to the orchestrator based on COMMAND_CATALOG."""

    def __init__(self, orchestrator: Any):
        self.orchestrator = orchestrator

    async def execute(self, action: ActionName, args: Details | None = None) -> Prompt:
        """Execute an action via the orchestrator.

        Args:
            action: Action name (key in COMMAND_CATALOG)
            args: Arguments dict for the action

        Returns:
            JSON string result (pydantic model dumped) or plain text wrapped in Prompt
        """
        if args is None:
            args = {}

        # Validate action name format
        validation_error = self._validate_action_name(str(action))
        if validation_error:
            return Prompt(validation_error)

        # Validate and sanitize arguments
        if not isinstance(args, dict):
            return Prompt(f"Error: 'args' must be a dictionary, got {type(args).__name__}.")
        args = self._sanitize_args(args)

        # Get command spec from catalog
        spec = self._get_command_spec(str(action))
        if spec is None:
            return Prompt(f"Error: Unknown action '{action}'. Use list_commands() to discover.")

        # Extract capability reference: "Protocol.method_name"
        capability_ref = spec.get("capability", "")
        if "." not in capability_ref:
            return Prompt(f"Error: Invalid capability format for action '{action}'.")

        protocol_name, method_name = capability_ref.rsplit(".", 1)

        # Resolve capability from the DI container/orchestrator
        try:
            cap = self._resolve_capability(protocol_name)
        except Exception as e:
            return Prompt(f"Error resolving capability '{protocol_name}' for action '{action}': {e}")

        if cap is None:
            return Prompt(f"Error: No capability matched protocol '{protocol_name}' for action '{action}'.")

        # Get method from capability
        if not hasattr(cap, method_name):
            return Prompt(f"Error: Capability '{protocol_name}' has no method '{method_name}' for action '{action}'.")

        method = getattr(cap, method_name)

        # Call the method with **args
        try:
            result = await method(**args)
            return Prompt(self._serialize_result(result))
        except Exception as e:
            import json

            return Prompt(json.dumps({"error": str(e), "action": str(action)}, indent=2))

    def _resolve_capability(self, protocol_name: str) -> Any | None:
        """Dynamically resolve the correct capability class from the orchestrator."""
        if protocol_name == "BlenderPort":
            return self.orchestrator.blender
        elif protocol_name == "SceneOperateProtocol":
            return self.orchestrator.operate_scene_capability
        elif protocol_name == "AssetSearchProtocol" or protocol_name == "AssetProviderPort":
            return self.orchestrator.search_asset_capability
        elif protocol_name == "GenerationProviderPort":
            return self.orchestrator.generate_ai_capability
        elif protocol_name == "ObjectOperateProtocol":
            return self.orchestrator.object_operate_capability
        elif protocol_name == "RenderOperateProtocol":
            return self.orchestrator.render_operate_capability
        elif protocol_name == "ImportExportProtocol":
            return self.orchestrator.import_export_capability
        return None

    def _serialize_result(self, result: Any) -> str:
        """Serialize capability method execution result to standard string or JSON."""
        if hasattr(result, "model_dump_json"):
            s: str = result.model_dump_json(indent=2)
            return s
        if isinstance(result, dict):
            import json

            return json.dumps(result, indent=2, default=str)
        return str(result)

    def _get_command_spec(self, action: str) -> CommandSpec | None:
        """Retrieve command spec from COMMAND_CATALOG."""
        return CommandCatalog.COMMAND_CATALOG.get(action)

    @staticmethod
    def _validate_action_name(action: str) -> str | None:
        """Validate action name format. Returns error message or None."""
        if not action or not action.strip():
            return "Error: Action name cannot be empty."
        if len(action) > MAX_ACTION_NAME_LENGTH:
            return f"Error: Action name exceeds {MAX_ACTION_NAME_LENGTH} characters."
        if not ACTION_NAME_PATTERN.match(action):
            return (
                f"Error: Invalid action name '{action}'. "
                f"Must be lowercase alphanumeric with underscores (e.g. 'get_scene_info')."
            )
        return None

    @staticmethod
    def _sanitize_args(args: Details) -> Details:
        """Sanitize argument values: strip strings, enforce length limits."""
        sanitized: Details = {}
        for key, value in args.items():
            if isinstance(value, str):
                value = value.strip()
                if len(value) > MAX_STRING_ARG_LENGTH:
                    logger.warning(
                        "Argument '%s' truncated from %d to %d chars",
                        key,
                        len(value),
                        MAX_STRING_ARG_LENGTH,
                    )
                    value = value[:MAX_STRING_ARG_LENGTH]
            sanitized[key] = value
        return sanitized
