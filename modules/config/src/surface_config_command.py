"""Config surface — CLI adapter for ``aa config …``.

AES surface-layer command adapter: turns raw CLI tokens into a typed
``ConfigRequest`` and calls the aggregate's single ``execute``; the agent
routes it to the right capability operation. Rendering (print / exit code)
lives here; domain work is delegated.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from modules.shared.src.contract_config_aggregate import IConfigAggregate
from modules.shared.src.taxonomy_common_vo import (
    ConfigData,
    ConfigFormat,
    ConfigKeys,
    ConfigOp,
    ConfigRequest,
    ConfigResult,
    EnvPairs,
    McpServersMap,
)


class ConfigCommand(IConfigAggregate):
    """CLI surface command for the config feature (surface layer, AES406)."""

    def __init__(self, orch: IConfigAggregate) -> None:
        self._orch = orch

    def execute(self, request: ConfigRequest) -> ConfigResult:
        """Delegate *request* to the wrapped aggregate unchanged."""
        return self._orch.execute(request)


def _fail(op: str, result: ConfigResult) -> int:
    """Report a failed ``ConfigResult`` on stderr and return the CLI exit code."""
    print(f"aa config {op}: {result.message}", file=sys.stderr)
    return 1


def cmd_config(args: list[str], orch: IConfigAggregate) -> int:
    """aa config load|save|merge_servers|set_env|remove_entries|inspect|help."""
    argv = list(args or [])
    if argv and argv[0] == "config":
        argv = argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(orch.execute(ConfigRequest(ConfigOp("help"))).data)
        return 0

    op = argv[0]
    try:
        if op == "load":
            result = orch.execute(ConfigRequest(ConfigOp("load"), path=Path(argv[1])))
            if not result.success:
                return _fail(op, result)
            data, fmt = result.data
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
            result = orch.execute(
                ConfigRequest(ConfigOp("save"), path=path, data=ConfigData(data), fmt=fmt)
            )
            return 0 if result.success else _fail(op, result)
        if op == "merge_servers":
            servers = McpServersMap(json.loads(argv[2]))
            result = orch.execute(
                ConfigRequest(ConfigOp("merge_servers"), path=Path(argv[1]), servers=servers)
            )
            if not result.success:
                return _fail(op, result)
            print("\n".join(result.data))
            return 0
        if op == "set_env":
            pairs = EnvPairs(json.loads(argv[2]))
            result = orch.execute(
                ConfigRequest(ConfigOp("set_env"), path=Path(argv[1]), pairs=pairs)
            )
            return 0 if result.success else _fail(op, result)
        if op == "remove_entries":
            dry = "--dry-run" in argv
            positional = [a for a in argv[1:] if not a.startswith("--")]
            path = Path(positional[0])
            keys = ConfigKeys(positional[1:])
            result = orch.execute(
                ConfigRequest(
                    ConfigOp("remove_entries"),
                    path=path,
                    keys=keys,
                    dry_run=dry,
                )
            )
            if not result.success:
                return _fail(op, result)
            print("\n".join(result.data))
            return 0
        if op == "inspect":
            result = orch.execute(ConfigRequest(ConfigOp("inspect"), path=Path(argv[1])))
            if not result.success:
                return _fail(op, result)
            print(json.dumps(result.data, indent=2, ensure_ascii=False, default=str))
            return 0
    except (OSError, ValueError, RuntimeError, TypeError, KeyError, IndexError) as exc:
        print(f"aa config {op}: {exc}", file=sys.stderr)
        return 1

    print(f"Unknown config op: {op}", file=sys.stderr)
    print(orch.execute(ConfigRequest(ConfigOp("help"))).data, file=sys.stderr)
    return 1
