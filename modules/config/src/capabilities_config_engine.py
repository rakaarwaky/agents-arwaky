"""Config engine capability — writer + modifier behind a single ``execute``.

Pure I/O helpers live in :mod:`modules.shared.src.utility_config_engine`
(utility layer, shared with harness capabilities under AES201). Both classes
implement the collapsed ``IConfigProtocol.execute`` dispatcher; the config
agent is their only caller.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from modules.shared.src.contract_config_protocol import IConfigProtocol
from modules.shared.src.taxonomy_common_vo import (
    ConfigData,
    ConfigFormat,
    ConfigTuple,
    EnvPairs,
    McpServersMap,
    Timestamp,
)
from modules.shared.src.utility_config_engine import (
    arwaky_server_names,
    detect_format,
    list_mcp_servers,
    load_file,
    merge_mcp_servers,
    remove_env_keys,
    remove_mcp_servers,
    save_file,
    set_env_keys,
)
from modules.shared.src.utility_jsonc_parser import strip_jsonc_comments
from modules.shared.src.utility_toml_write import write_toml


# ─── Block 1: Class Definition & Constructor ──────────────
class ConfigWriter(IConfigProtocol):
    """Load / detect / save capability (single-execute dispatcher)."""

    # ─── Block 2: Protocol ABC Method Implementation ──────────
    def execute(
        self,
        op: str,
        path: Path,
        payload: dict | None = None,
    ) -> ConfigTuple | bool | ConfigFormat:
        if op == "load":
            return self.load_file(path)
        if op == "save":
            body = payload or {}
            fmt = body.get("fmt")
            if fmt is not None:
                fmt = ConfigFormat(fmt)
            return self.save_file(path, ConfigData(body.get("data", {})), fmt)
        if op == "detect_format":
            return self.detect_format(path)
        raise ValueError(f"ConfigWriter does not support op {op!r}")

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def load_file(self, path: Path) -> ConfigTuple:
        data, fmt = load_file(path)
        return (ConfigData(data), ConfigFormat(fmt))

    def save_file(
        self,
        path: Path,
        data: ConfigData,
        fmt: ConfigFormat | None = None,
    ) -> bool:
        if fmt is None:
            fmt = ConfigFormat(detect_format(path))
        return save_file(path, data, fmt)

    def detect_format(self, path: Path) -> ConfigFormat:
        return ConfigFormat(detect_format(path))

    def normalize_jsonc(self, text: str) -> str:
        return strip_jsonc_comments(text)

    def dumps_toml(self, data) -> str:
        return write_toml(data)


# ─── Block 1: Class Definition & Constructor ──────────────
class ConfigModifier(IConfigProtocol):
    """Merge / env-set / removal / list capability (single-execute dispatcher)."""

    # ─── Block 2: Protocol ABC Method Implementation ──────────
    def execute(
        self,
        op: str,
        path: Path,
        payload: dict | None = None,
    ) -> list[str] | None:
        if op == "merge_servers":
            body = payload or {}
            return self.merge_mcp_servers(
                path,
                McpServersMap(body.get("servers", {})),
                bool(body.get("force", False)),
            )
        if op == "set_env":
            body = payload or {}
            return self.set_env_keys(path, EnvPairs(body.get("pairs", {})))
        if op == "remove_entries":
            body = payload or {}
            keys = list(body.get("keys", ()))
            dry = bool(body.get("dry_run", False))
            if self._looks_like_env(path):
                return self.remove_env_keys(path, keys, dry)
            return self.remove_mcp_servers(path, keys, dry)
        if op == "list_servers":
            return self.list_mcp_servers(path)
        raise ValueError(f"ConfigModifier does not support op {op!r}")

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def remove_mcp_servers(
        self,
        path: Path,
        servers: list[str],
        dry_run: bool = False,
    ) -> list[str]:
        return remove_mcp_servers(path, servers, dry_run)

    def remove_env_keys(
        self,
        path: Path,
        keys: list[str],
        dry_run: bool = False,
    ) -> list[str]:
        return remove_env_keys(path, keys, dry_run)

    def list_mcp_servers(self, path: Path) -> list[str]:
        return list_mcp_servers(path)

    def merge_mcp_servers(
        self,
        path: Path,
        servers: McpServersMap,
        force: bool = False,
    ) -> list[str]:
        return merge_mcp_servers(path, servers, force)

    def set_env_keys(self, path: Path, pairs: EnvPairs) -> None:
        set_env_keys(path, pairs)

    @staticmethod
    def _looks_like_env(path: Path) -> bool:
        name = path.name.lower()
        return name.startswith(".env") or name.endswith(".env")


def main(argv):
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
    "ConfigData",
    "ConfigFormat",
    "ConfigModifier",
    "ConfigTuple",
    "ConfigWriter",
    "EnvPairs",
    "IConfigProtocol",
    "McpServersMap",
    "Timestamp",
    "arwaky_server_names",
    "detect_format",
    "list_mcp_servers",
    "load_file",
    "main",
    "merge_mcp_servers",
    "remove_env_keys",
    "remove_mcp_servers",
    "save_file",
    "set_env_keys",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ConfigData": ConfigData,
    "ConfigFormat": ConfigFormat,
    "ConfigModifier": ConfigModifier,
    "ConfigTuple": ConfigTuple,
    "ConfigWriter": ConfigWriter,
    "EnvPairs": EnvPairs,
    "IConfigProtocol": IConfigProtocol,
    "McpServersMap": McpServersMap,
    "Timestamp": Timestamp,
}
