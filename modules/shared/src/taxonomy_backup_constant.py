"""Backup-domain constants — tool -> XDG data-subdir mapping (AES layer: taxonomy)."""

#: tool id -> XDG data subdirectory (relative to XDG_DATA_HOME) covered by backup.
TOOL_DATA: dict[str, str] = {
    "anytype": "anytype-mcp",
    "9router": "9router",
    "mnemosyne": "mnemosyne",
    "google-workspace": "google-workspace-mcp",
}
