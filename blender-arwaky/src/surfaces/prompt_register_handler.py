"""MCP Prompts for BlenderMCP"""

from mcp.server.fastmcp import FastMCP

from agent.system_prompt_manager import (
    get_layout_expert_prompt,
    get_lighting_expert_prompt,
    get_text_to_scene_orchestrator_prompt,
)
from contract import SystemPromptManagerAggregate


class PromptHandlerModule:
    """Handler for MCP prompt registration."""

    _contract_ref: SystemPromptManagerAggregate

    @staticmethod
    def asset_creation_strategy():
        """Defines the preferred strategy for creating assets in Blender"""
        return [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": """Create a Blender asset using the best available strategy.
When creating 3D content in Blender, always start by checking if integrations are available:

0. Before anything, always check the tool_scene_ops from get_scene_info()
1. First use the following tools to verify if the following integrations are enabled:
    1. Poly Haven
        Use get_polyhaven_status() to verify its status ...
Only fall back to scripting when:
- Poly Haven, Sketchfab, Hyper3D, and Hunyuan3D are all disabled
- A simple primitive is explicitly requested
- No suitable asset exists in any of the libraries
- Hyper3D Rodin or Hunyuan3D failed to generate the desired asset
- The task specifically requires a basic material/color
""",
                },
            }
        ]

    @staticmethod
    def lighting_expert():
        return [{"role": "user", "content": {"type": "text", "text": get_lighting_expert_prompt()}}]

    @staticmethod
    def layout_expert():
        return [{"role": "user", "content": {"type": "text", "text": get_layout_expert_prompt()}}]

    @staticmethod
    def text_to_scene_orchestrator():
        return [{"role": "user", "content": {"type": "text", "text": get_text_to_scene_orchestrator_prompt()}}]

    @staticmethod
    def register_prompts(mcp: FastMCP):
        mcp.prompt(name="asset_creation_strategy")(PromptHandlerModule.asset_creation_strategy)
        mcp.prompt(name="lighting_expert")(PromptHandlerModule.lighting_expert)
        mcp.prompt(name="layout_expert")(PromptHandlerModule.layout_expert)
        mcp.prompt(name="text_to_scene_orchestrator")(PromptHandlerModule.text_to_scene_orchestrator)


# Module-level alias for backward compatibility
asset_creation_strategy = PromptHandlerModule.asset_creation_strategy
register_prompts = PromptHandlerModule.register_prompts
