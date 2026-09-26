"""Config modifier capability — merge / set env / remove.

Thin AES capability wrapping the shared config kernel. The config agent
(``agent_config_orchestrator``) is the only caller; no I/O outside the
injected protocol. Implements ``IConfigModifierProtocol`` exclusively — the
read operations live on ``ConfigWriter`` under its own seam. ``main``
provides a standalone CLI for the same operations.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from modules.shared.src.contract_config_protocol import IConfigModifierProtocol
from modules.shared.src.taxonomy_common_vo import (
    ConfigKeys,
    EnvPairs,
    HelpText,
    McpServersMap,
)
from modules.shared.src.utility_config_engine import (
    arwaky_server_names,
    list_mcp_servers,
    merge_mcp_servers,
    remove_env_keys,
    remove_mcp_servers,
    set_env_keys,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class ConfigModifier(IConfigModifierProtocol):
    """Merge / env-set / removal capability."""

    def __init__(self, usage: HelpText | None = None) -> None:
        self._usage = usage if usage is not None else HelpText("")

    # ─── Block 2: Protocol Method Implementation ──────────────
    def merge_servers(
        self,
        path: Path,
        servers: McpServersMap,
    ) -> ConfigKeys:
        """Merge *servers* into *path*; returns merged server names."""
        return self.merge_mcp_servers(path, servers)

    def set_env(self, path: Path, pairs: EnvPairs) -> None:
        """Upsert *pairs* into the env file at *path*."""
        self.set_env_keys(path, pairs)

    def remove_entries(
        self,
        path: Path,
        keys: ConfigKeys,
        dry_run: bool = False,
    ) -> ConfigKeys:
        """Drop named entries from *path*; env or MCP depending on the file name."""
        return self.remove_mcp_servers(
            path,
            list(keys),
            dry_run,
        ) if not self._looks_like_env(path) else self.remove_env_keys(
            path,
            list(keys),
            dry_run,
        )

    def help(self) -> HelpText:
        """Return the usage text the agent injected."""
        return self._usage

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return "ConfigModifier()"

    def remove_mcp_servers(
        self,
        path: Path,
        servers: list[str],
        dry_run: bool = False,
    ) -> list[str]:
        """Remove named MCP servers from *path*, optionally dry-run."""
        return remove_mcp_servers(path, servers, dry_run)

    def remove_env_keys(
        self,
        path: Path,
        keys: list[str],
        dry_run: bool = False,
    ) -> list[str]:
        """Remove named env keys from *path*, optionally dry-run."""
        return remove_env_keys(path, keys, dry_run)

    def list_mcp_servers(self, path: Path) -> list[str]:
        """Return the list of MCP server names in *path*."""
        return list_mcp_servers(path)

    def merge_mcp_servers(
        self,
        path: Path,
        servers: McpServersMap,
        force: bool = False,
    ) -> list[str]:
        """Merge *servers* into *path*, returning merged server names."""
        return merge_mcp_servers(path, servers, force)

    def set_env_keys(self, path: Path, pairs: EnvPairs) -> None:
        """Upsert *pairs* into the env file at *path*."""
        set_env_keys(path, pairs)

    @staticmethod
    def _looks_like_env(path: Path) -> bool:
        """Return whether *path* is an env-style ``KEY=VALUE`` file by name."""
        name = path.name.lower()
        return name.startswith(".env") or name.endswith(".env")


def main(argv):
    """Entry point for standalone execution of ConfigModifier operations."""
    if len(argv) < 2 or argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd = argv[1]
    if cmd == "remove-mcp-servers":
        file = Path(argv[2])
        servers = argv[3:]
        dry = "--dry-run" in servers
        servers = [s for s in servers if s != "--dry-run"]
        removed = remove_mcp_servers(file, servers, dry)
        print("\n".join(removed))
        return 0
    if cmd == "remove-env-keys":
        file = Path(argv[2])
        keys = argv[3:]
        dry = "--dry-run" in keys
        keys = [k for k in keys if k != "--dry-run"]
        removed = remove_env_keys(file, keys, dry)
        print("\n".join(removed))
        return 0
    if cmd == "list-mcp-servers":
        file = Path(argv[2])
        print("\n".join(list_mcp_servers(file)))
        return 0
    if cmd == "merge-mcp-servers":
        file = Path(argv[2])
        json_payload = argv[3]
        force = "--force" in argv
        servers = json.loads(json_payload)
        merged = merge_mcp_servers(file, servers, force)
        print("\n".join(merged))
        return 0
    if cmd == "set-env-keys":
        file = Path(argv[2])
        json_payload = argv[3]
        pairs = json.loads(json_payload)
        set_env_keys(file, pairs)
        return 0
    if cmd == "arwaky-server-names":
        repo = Path(argv[2]) if len(argv) > 2 else Path(os.getcwd())
        print("\n".join(arwaky_server_names(repo)))
        return 0
    print(f"Unknown command: {cmd}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))


__all__ = [
    "ConfigModifier",
    "main",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ConfigModifier": ConfigModifier,
    "EnvPairs": EnvPairs,
    "IConfigModifierProtocol": IConfigModifierProtocol,
    "McpServersMap": McpServersMap,
}
