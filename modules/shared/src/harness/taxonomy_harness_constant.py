"""Harness-domain constants — alias table + supported set (taxonomy layer).

Pure data: the alias table maps raw CLI tokens (ids / aliases) onto canonical
harness ids. Unknown tokens are surfaced to the CLI, never raised here.
"""
from __future__ import annotations

#: canonical harness id -> raw CLI tokens that resolve to it (id itself + aliases).
HARNESSES: dict[str, tuple[str, ...]] = {
    "hermes": ("hermes",),
    "opencode": ("opencode",),
    "grok-build": ("grok-build", "grok"),
}

ALIASES: dict[str, str] = {}
for _harness_id, _tokens in HARNESSES.items():
    for _token in _tokens:
        ALIASES[_token] = _harness_id

ALL_HARNESS_IDS: tuple[str, ...] = tuple(HARNESSES)

#: Credential values that stand in for a real gateway key (OmniRoute or
#: 9router); env injection and the live probe both skip a key equal to one
#: of these.
PLACEHOLDER_KEYS: frozenset[str] = frozenset({
    "sk-your-9router-consumer-key-here", "<YOUR_API_KEY>", "change-me", "",
})

#: Server id -> launcher command used when mcp_servers.generated.json is
#: absent, so `aa connect` still writes a runnable command per server.
FALLBACK_MCP_COMMANDS: dict[str, str] = {
    "codegraph": "codegraph-mcp",
    "vision-arwaky": "vision-arwaky-mcp",
    "qwen-web-arwaky": "qwen-web-mcp",
    "blender-arwaky": "blender-mcp",
    "lint-arwaky": "lint-arwaky-mcp",
    "workspace": "workspace-mcp",
}

#: Per-skill sub-directories copied alongside SKILL.md on snapshot installs.
ASSET_DIRS: tuple[str, ...] = (
    "scripts", "references", "resources", "examples", "templates", "assets",
)

#: Filenames a live Hermes profile's skills dir holds as runtime state. They
#: belong to the profile, NOT the shared pack — migrating them in would
#: pollute the pack with per-profile usage/curator state. Their presence marks
#: a live home whose leftovers must be preserved in place (backed up), not
#: moved.
LIVE_SKILLS_STATE: frozenset[str] = frozenset({
    ".usage.json", ".usage.json.lock", ".curator_state", ".bundled_manifest",
})

__all__ = [
    "ALIASES",
    "ALL_HARNESS_IDS",
    "ASSET_DIRS",
    "FALLBACK_MCP_COMMANDS",
    "HARNESSES",
    "LIVE_SKILLS_STATE",
    "PLACEHOLDER_KEYS",
]
