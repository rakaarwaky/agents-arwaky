"""Tool-domain constants for the unified tools feature.

Sentinels, daemon-tool ids, runner-family lookup, and the per-tool
launcher/alias tables shared by the lifecycle capabilities and adapters.
"""
from modules.shared.src.taxonomy_core_constant import TOOL_RUNNERS

#: Reserved non-zero exit code: "executable vanished between discovery and launch".
SENTINEL_EXECUTABLE_GONE = 126

#: Tool ids that are long-running daemons (container isolation invariant).
DAEMON_TOOL_IDS: frozenset[str] = frozenset({"9router", "anytype", "anytype-daemon"})

#: Runner families a tool installs through (cargo / uv / bun / pnpm / npm / pip-venv).
RUNNER_FAMILIES = ("cargo", "uv", "python", "bun", "pnpm", "npm")

# Tool ids that have a systemd user unit managed under $XDG_CONFIG_HOME.
DAEMON_UNIT_TOOLS: dict[str, str] = {
    "9router": "9router.service",
    "anytype-daemon": "anytype-daemon.service",
}

# Tool id -> daemon feature name (keyed on manifest id; "anytype-daemon"
# routes to the "anytype" daemon manager in the daemon orchestrator).
DAEMON_NAMES: dict[str, str] = {
    "9router": "9router",
    "anytype-daemon": "anytype",
}

# Per-tool launcher/alias names the installer registers under $XDG_BIN_HOME.
# Data source for the remover capability's generic teardown.
LAUNCHER_NAMES: dict[str, list[str]] = {
    "anytype": ["anytype-mcp", "anytype-daemon", "ad"],
    "anytype-daemon": ["anytype-daemon", "ad"],
    "blender": ["blender-arwaky", "ba", "blender-mcp"],
    "codegraph": ["codegraph-mcp", "codegraph"],
    "context7": ["context7-mcp", "ctx7"],
    "fetch": ["fetch-mcp", "mcp-fetch"],
    "lint": ["lint-arwaky", "la", "lint-arwaky-cli", "lint-arwaky-mcp", "lint-arwaky-tui", "lac"],
    "mnemosyne": ["mnemosyne", "mnemosyne-mcp"],
    "9router": ["9router"],
    "ponytail": ["ponytail-mcp"],
    "qwen-web": ["qwen-web-arwaky", "qwa", "qwen-web-cli", "qwen-web-mcp", "qwc"],
    "skill": ["skill.py", "skills"],
    "vision": ["vision-arwaky", "vision-arwaky-cli", "va", "vision-arwaky-mcp"],
    "workspace": ["workspace-mcp", "google-workspace-mcp"],
}

# Tool id -> manifest alias (short form; used for alias-targeted operations).
ALIAS_TABLE: dict[str, str | None] = {
    "anytype-daemon": "ad",
    "workspace": "google-workspace",
    "mnemosyne": "mnemosyne-memory",
    "vision": "va",
    "qwen-web": "qwa",
    "lint": "la",
    "blender": "ba",
    "skill": "skills",
}


__all__ = [
    "ALIAS_TABLE",
    "DAEMON_NAMES",
    "DAEMON_TOOL_IDS",
    "DAEMON_UNIT_TOOLS",
    "LAUNCHER_NAMES",
    "RUNNER_FAMILIES",
    "SENTINEL_EXECUTABLE_GONE",
    "TOOL_RUNNERS",
]
