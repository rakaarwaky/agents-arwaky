"""Config surface — CLI adapter for ``aa config …``.

AES surface-layer command adapter: one class implementing the aggregate
surface while staying free of root/capability/agent imports (AES201/AES205).
Rendering (print / exit code) lives here; domain work is delegated.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from modules.shared.src.contract_config_aggregate import IConfigAggregate
from modules.shared.src.taxonomy_common_vo import (
    ConfigData,
    ConfigFormat,
    ConfigSnapshot,
    EnvPairs,
    HelpText,
    McpServersMap,
)


class ConfigCommand(IConfigAggregate):
    """CLI surface command for the config feature (surface layer, AES406)."""

    def __init__(self, orch: IConfigAggregate) -> None:
        self._orch = orch

    def load(self, path: Path):
        """Load config data from *path* via the orchestrator."""
        return self._orch.load(path)

    def save(self, path, data, fmt=None):
        """Save *data* to *path* via the orchestrator, optionally overriding *fmt*."""
        return self._orch.save(path, data, fmt)

    def merge_servers(self, path, servers):
        """Merge *servers* into the config at *path* via the orchestrator."""
        return self._orch.merge_servers(path, servers)

    def set_env(self, path, pairs):
        """Upsert *pairs* into the env file at *path* via the orchestrator."""
        return self._orch.set_env(path, pairs)

    def remove_entries(self, path, keys, dry_run=False):
        """Remove named entries from *path* via the orchestrator, optionally dry-run."""
        return self._orch.remove_entries(path, keys, dry_run)

    def inspect(self, path: Path) -> ConfigSnapshot:
        """Return a read-only snapshot of the config at *path* via the orchestrator."""
        return self._orch.inspect(path)

    def help(self) -> HelpText:
        """Return usage text via the orchestrator."""
        return self._orch.help()


def cmd_config(args: list[str], orch: IConfigAggregate) -> int:
    """aa config load|save|merge_servers|set_env|remove_entries|inspect|help."""
    argv = list(args or [])
    if argv and argv[0] == "config":
        argv = argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(orch.help())
        return 0

    op = argv[0]
    try:
        if op == "load":
            data, fmt = orch.load(Path(argv[1]))
            print(
                json.dumps(
                    {"format": str(fmt), "data": data},
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 0
        if op == "save":
            path = Path(argv[1])
            data = json.loads(argv[2])
            fmt = None
            if "--fmt" in argv:
                fmt = ConfigFormat(argv[argv.index("--fmt") + 1])
            return 0 if orch.save(path, ConfigData(data), fmt) else 1
        if op == "merge_servers":
            servers = McpServersMap(json.loads(argv[2]))
            merged = orch.merge_servers(Path(argv[1]), servers)
            print("\n".join(merged))
            return 0
        if op == "set_env":
            pairs = EnvPairs(json.loads(argv[2]))
            orch.set_env(Path(argv[1]), pairs)
            return 0
        if op == "remove_entries":
            dry = "--dry-run" in argv
            positional = [a for a in argv[1:] if not a.startswith("--")]
            path = Path(positional[0])
            keys = positional[1:]
            removed = orch.remove_entries(path, keys, dry_run=dry)
            print("\n".join(removed))
            return 0
        if op == "inspect":
            snap = orch.inspect(Path(argv[1]))
            print(json.dumps(snap, indent=2, ensure_ascii=False, default=str))
            return 0
    except (OSError, ValueError, RuntimeError, TypeError, KeyError, IndexError) as exc:
        print(f"aa config {op}: {exc}", file=sys.stderr)
        return 1

    print(f"Unknown config op: {op}", file=sys.stderr)
    print(orch.help(), file=sys.stderr)
    return 1
