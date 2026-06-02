"""Handlers Layer: MCP command handler exports.

All handler modules are flat and follow 3-word snake_case naming.
These are the entry points exposed to the MCP gateway.
"""

from .catalog_command_handler import CommandCatalogSurfaceHandler
from .cli_command_handler import CliCommandHandler
from .command_execute_handler import CommandExecuteHandler
from .commands_list_handler import CommandsListHandler
from .health_check_handler import HealthCheckHandler
from .prompt_register_handler import PromptHandlerModule, register_prompts
from .server_instance_handler import ServerInstanceHandler
from .server_start_handler import ServerStartHandler
from .skill_read_handler import SkillReadHandler
from .status_check_handler import StatusCheckHandler
from .tool_registry_handler import ToolRegistryHandler, register_tools

__all__ = [
    "CommandCatalogSurfaceHandler",
    "CliCommandHandler",
    "CommandExecuteHandler",
    "CommandsListHandler",
    "HealthCheckHandler",
    "PromptHandlerModule",
    "register_prompts",
    "ServerInstanceHandler",
    "ServerStartHandler",
    "SkillReadHandler",
    "StatusCheckHandler",
    "ToolRegistryHandler",
    "register_tools",
]

# Note: ServerStartHandler is intentionally NOT exported from barrel.
# Import it directly: from src.surfaces.server_start_handler import ServerStartHandler
