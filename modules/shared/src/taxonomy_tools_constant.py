"""Tool-domain constants for the unified tools feature.

Sentinels, daemon-tool ids, runner-family lookup, the per-tool
launcher/alias tables, and the per-tool path/recipe literals shared by
the lifecycle capabilities and the adapter (extracted from
`capabilities_tools_adapter.py` — pure compile-time data only).
"""

#: Reserved non-zero exit code: "executable vanished between discovery and launch".
SENTINEL_EXECUTABLE_GONE = 126

#: Tool ids that are long-running daemons (container isolation invariant).
DAEMON_TOOL_IDS: frozenset[str] = frozenset({"9router", "anytype", "anytype-daemon"})

#: Runner families a tool installs through (cargo / uv / bun / pnpm / npm / pip-venv).
RUNNER_FAMILIES = ("cargo", "uv", "python", "bun", "pnpm", "npm")

# Tool ids that have a systemd user unit managed under $XDG_CONFIG_HOME.
# P1-5: the merged `anytype` id owns the daemon half too — uninstall must
# stop the unit (or name it as a residual), not just delete its launcher.
DAEMON_UNIT_TOOLS: dict[str, str] = {
    "9router": "9router.service",
    "anytype": "anytype-daemon.service",
    "anytype-daemon": "anytype-daemon.service",
}

# Tool id -> daemon feature name (keyed on manifest id; "anytype-daemon"
# routes to the "anytype" daemon manager in the daemon orchestrator).
DAEMON_NAMES: dict[str, str] = {
    "9router": "9router",
    "anytype": "anytype",
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
    "vision": ["vision-arwaky", "vision-arwaky-cli", "va", "vision-arwaky-mcp"],
    "workspace": ["workspace-mcp", "google-workspace-mcp"],
}

# Tool ids whose XDG config subtree is NOT installer-owned and is kept on
# removal (anytype-daemon keeps its config: the daemon owns it across updates).
KEEP_CONFIG: frozenset[str] = frozenset({"anytype-daemon"})

# Tool id -> manifest alias (short form; used for alias-targeted operations).
ALIAS_TABLE: dict[str, str | None] = {
    "anytype-daemon": "ad",
    "workspace": "google-workspace",
    "mnemosyne": "mnemosyne-memory",
    "vision": "va",
    "qwen-web": "qwa",
    "lint": "la",
    "blender": "ba",
}

# ── Adapter recipe literals (extracted from capabilities_tools_adapter.py) ──

#: Node-family default copy ignores when a tool recipe omits `ignores`.
NODE_IGNORES: tuple[str, ...] = (
    "node_modules", ".git", "__pycache__", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
)

#: Canonical registered name of the qwen-web tool.
QWEN_TOOL_NAME = "qwen-web"

#: First-line env var every generated launcher reads for the repo root.
ROOT_ENV_VAR = "AGENTS_ARWAKY_ROOT"

#: Install-stamp filename recorded next to a deployed venv/app.
INSTALL_STAMP_FILENAME = ".arwaky-install.json"

#: Remote branch probe order when a submodule has no symbolic HEAD.
FALLBACK_REMOTE_BRANCHES: tuple[str, ...] = ("main", "master", "dev")

#: Qwen-web queue role directories provisioned under the XDG data dir.
QWEN_ROLE_DIRS: tuple[str, ...] = (
    "role-architect", "role-business-analyst", "role-tech-lead",
)

#: pnpm flag appended to a context7 checkout so lifecycle builds run.
PNPM_DANGEROUS_ALLOW = "dangerouslyAllowAllBuilds"

#: Per-launcher entry points of the context7 build output.
CONTEXT7_LAUNCHER_ENTRIES: dict[str, str] = {
    "context7-mcp": "packages/mcp/dist/index.js",
    "ctx7": "packages/cli/dist/index.js",
}

#: fetch-mcp CLI sub-flags that select the CLI bundle over the MCP bundle.
FETCH_CLI_ARGS: frozenset[str] = frozenset({
    "html", "markdown", "readable", "txt", "json", "youtube",
    "--help", "-h", "--version", "-v",
})

# ── anytype (bun MCP + container daemon) ──
ANYTYPE_MCP_SRC_REL = "vendor/anytype-mcp"
ANYTYPE_MCP_APP_REL = "anytype-mcp"
ANYTYPE_MCP_ENTRY = "bin/cli.mjs"
ANYTYPE_DAEMON_DATA_REL = "anytype-daemon"
ANYTYPE_INTERNAL_BIN = "internal-bin"
ANYTYPE_VOLUME_DIRS: tuple[str, ...] = ("data", "dot-anytype", "config", "share")

# ── lint (cargo — rustup bootstrap + atomic install) ──
LINT_INTERNAL_DIR_REL = "internal/lint-arwaky"
LINT_BINARIES: tuple[str, ...] = (
    "lint-arwaky", "la", "lint-arwaky-cli", "lint-arwaky-mcp", "lint-arwaky-tui",
)
LINT_LAUNCHERS: tuple[tuple[str, str], ...] = (
    ("lint-arwaky", "lint-arwaky"),
    ("la", "la"),
    ("lint-arwaky-cli", "lint-arwaky-cli"),
    ("lint-arwaky-mcp", "lint-arwaky-mcp"),
    ("lint-arwaky-tui", "lint-arwaky-tui"),
    ("lac", "lac"),
)
#: NOTE: leaf lama merujuk `_BUILD_DEPS` tanpa definisi (NameError) — didefinisikan di sini.
LINT_BUILD_DEPS: tuple[tuple[str, str], ...] = (("sccache", "sccache"), ("mold", "mold"))

# ── 9router (host-native daemon + launcher) ──
NINEROUTER_DATA_DIR_NAME = "9router"
NINEROUTER_INTERNAL_BIN = "internal-bin"
NINEROUTER_LAUNCHERS: tuple[str, ...] = ("9router",)

#: Adapter action-prefix table for config-driven tools (backward-compat globals).
TOOL_ACTION_PREFIXES: dict[str, str] = {
    "blender": "blender",
    "vision": "vision",
    "qwen-web": "qwen_web",
    "mnemosyne": "mnemosyne",
    "workspace": "workspace",
    "codegraph": "codegraph",
    "context7": "context7",
    "fetch": "fetch",
    "ponytail": "ponytail",
}


__all__ = [
    "ALIAS_TABLE",
    "ANYTYPE_DAEMON_DATA_REL",
    "ANYTYPE_INTERNAL_BIN",
    "ANYTYPE_MCP_APP_REL",
    "ANYTYPE_MCP_ENTRY",
    "ANYTYPE_MCP_SRC_REL",
    "ANYTYPE_VOLUME_DIRS",
    "CONTEXT7_LAUNCHER_ENTRIES",
    "DAEMON_NAMES",
    "DAEMON_TOOL_IDS",
    "DAEMON_UNIT_TOOLS",
    "FALLBACK_REMOTE_BRANCHES",
    "FETCH_CLI_ARGS",
    "INSTALL_STAMP_FILENAME",
    "KEEP_CONFIG",
    "LAUNCHER_NAMES",
    "LINT_BINARIES",
    "LINT_BUILD_DEPS",
    "LINT_INTERNAL_DIR_REL",
    "LINT_LAUNCHERS",
    "NODE_IGNORES",
    "NINEROUTER_DATA_DIR_NAME",
    "NINEROUTER_INTERNAL_BIN",
    "NINEROUTER_LAUNCHERS",
    "PNPM_DANGEROUS_ALLOW",
    "QWEN_ROLE_DIRS",
    "QWEN_TOOL_NAME",
    "ROOT_ENV_VAR",
    "RUNNER_FAMILIES",
    "SENTINEL_EXECUTABLE_GONE",
    "TOOL_ACTION_PREFIXES",
]
