"""Config engine I/O (moved from tools/lib/engine.py).

Shared library for reading/writing agent harness configuration files:
JSON, JSONC (with // comments), YAML and TOML - with format auto-detection,
comment preservation (YAML via ruamel when available), and helpers for
removing agents-arwaky MCP servers / env keys.

CLI usage (standalone):
    python3 -m modules.config.src.capabilities_config_engine remove-mcp-servers <file> <s1> ...
"""
from __future__ import annotations

import json
import os
import re
import sys
import tomllib
from pathlib import Path

from modules.shared.src.config.contract_config_protocol import IConfigModifier, IConfigWriter
from modules.shared.src.config.utility_jsonc import strip_jsonc_comments
from modules.shared.src.config.utility_toml_write import write_toml

def detect_format(path: Path) -> str:
    name = path.name.lower()
    if name.endswith((".yaml", ".yml")):
        return "yaml"
    if name.endswith(".jsonc"):
        return "jsonc"
    if name.endswith((".json", ".bak")):
        return "json"
    if name.endswith(".toml"):
        return "toml"
    # Fallback: peek content
    try:
        text = path.read_text(encoding="utf-8", errors="replace")[:4096]
        if re.search(r"^\s*[-\w]+\s*:", text, re.MULTILINE):
            return "yaml"
    except OSError:
        pass
    return "json"



def load_file(path: Path):
    """Load JSON / JSONC / YAML / TOML into a dict. Returns ({}, fmt) on failure."""
    fmt = detect_format(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    if fmt in ("json", "jsonc"):
        if fmt == "jsonc":
            text = strip_jsonc_comments(text)
        try:
            return json.loads(text), fmt
        except json.JSONDecodeError:
            return {}, fmt
    if fmt == "toml":
        try:
            return tomllib.loads(text), fmt
        except Exception:
            return {}, fmt
    # YAML
    data = None
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(text) or {}
    except ImportError:
        data = None  # pyyaml not installed; try ruamel below
    except yaml.YAMLError:
        data = None  # malformed YAML; try ruamel below
    if data is not None:
        return data, fmt
    # ruamel fallback
    try:
        import ruamel.yaml  # type: ignore
        data = ruamel.yaml.YAML(typ="safe").load(text) or {}
        return data, fmt
    except ImportError:
        pass  # ruamel not installed
    except ruamel.yaml.YAMLError:
        pass  # malformed YAML
    return {}, fmt


def save_file(path: Path, data, fmt: str, preserve_comments: bool = True) -> bool:
    """Write dict back preserving format. Returns True on success."""
    try:
        if fmt == "json":
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        elif fmt == "jsonc":
            # Best-effort: preserve original JSONC comments outside modified blocks.
            # If original file exists, keep line comments (//) outside mcp/mcpServers sections.
            try:
                original = path.read_text(encoding="utf-8", errors="replace")
                comment_lines = [
                    ln for ln in original.splitlines()
                    if ln.strip().startswith("//") and "mcp" not in ln.lower()
                ]
            except OSError:
                comment_lines = []
            body = json.dumps(data, indent=2, ensure_ascii=False)
            if comment_lines:
                body = "\n".join(comment_lines) + "\n" + body
            path.write_text(body + "\n", encoding="utf-8")
        elif fmt == "toml":
            toml_text = write_toml(data)
            path.write_text(toml_text, encoding="utf-8")
        elif fmt == "yaml":
            dumped = False
            if preserve_comments:
                try:
                    import ruamel.yaml  # type: ignore
                    y = ruamel.yaml.YAML()
                    y.preserve_quotes = True
                    with path.open("w", encoding="utf-8") as f:
                        y.dump(data, f)
                    dumped = True
                except ImportError:
                    dumped = False  # ruamel unavailable; fall back to pyyaml
                except ruamel.yaml.YAMLError:
                    dumped = False  # ruamel dump failed; fall back to pyyaml
            if not dumped:
                import yaml  # type: ignore
                with path.open("w", encoding="utf-8") as f:
                    yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
        return True
    except (OSError, TypeError, ValueError, ImportError):
        return False


# ---------------------------------------------------------------------------
# MCP server helpers
# ---------------------------------------------------------------------------
def get_mcp_map(data: dict):
    """Return the dict holding MCP servers (mcpServers, mcp, or mcp_servers)."""
    if isinstance(data, dict):
        if isinstance(data.get("mcpServers"), dict):
            return data["mcpServers"], "mcpServers"
        if isinstance(data.get("mcp"), dict):
            return data["mcp"], "mcp"
        if isinstance(data.get("mcp_servers"), dict):
            return data["mcp_servers"], "mcp_servers"
    return None, None


def remove_mcp_servers(path: Path, servers, dry_run: bool = False) -> list:
    """Remove the given server names from the file's MCP map (with backup).

    Returns list of actually-removed server names.
    """
    if not path.exists():
        return []
    data, fmt = load_file(path)
    mcp, _ = get_mcp_map(data)
    removed = []
    if mcp is not None:
        for s in servers:
            if s in mcp:
                mcp.pop(s)
                removed.append(s)
    if removed and not dry_run:
        # Backup original before mutating (S8: no silent config loss) + rotation (max 3)
        try:
            backup = path.with_name(path.name + ".bak-arwaky")
            backup.write_text(path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
            # Rotate: keep only the 3 most recent backups
            backups = sorted(path.parent.glob(path.name + ".bak-arwaky*"))
            for stale in backups[:-3]:
                stale.unlink(missing_ok=True)
        except OSError:
            pass
        save_file(path, data, fmt)
    return removed


def list_mcp_servers(path: Path):
    if not path.exists():
        return []
    data, _ = load_file(path)
    mcp, _ = get_mcp_map(data)
    if mcp is None:
        return []
    return list(mcp.keys())


# ---------------------------------------------------------------------------
# Env key helpers
# ---------------------------------------------------------------------------
def remove_env_keys(path: Path, keys, dry_run: bool = False) -> list:
    """Remove `KEY=...` lines from a .env-style file. Returns removed keys.

    Delegates to envfile.remove_env_keys for the core logic.
    """
    from modules.shared.src.envfile.utility_envfile import remove_env_keys as _envfile_remove
    if dry_run:
        from modules.shared.src.envfile.utility_envfile import parse_env_file
        env = parse_env_file(path)
        return [k for k in keys if k in env]
    return _envfile_remove(path, keys)


# ---------------------------------------------------------------------------
# agents-arwaky server list (single source of truth)
# ---------------------------------------------------------------------------
def default_server_names() -> list:
    """Server names generated by modules/mcp/src/capabilities_mcp_generator.py (static fallback)."""
    return [
        "context7", "fetch", "ponytail", "anytype", "codegraph",
        "vision", "qwen-web", "blender", "lint", "workspace", "mnemosyne",
    ]


def arwaky_server_names(repo_root: Path) -> list:
    """Read server names from mcp_servers.generated.json if present, else fallback."""
    gen = repo_root / "mcp_servers.generated.json"
    if gen.exists():
        try:
            data = json.loads(gen.read_text(encoding="utf-8"))
            keys = list(data.get("mcpServers", {}).keys())
            if keys:
                return keys
        except (OSError, ValueError):
            pass
    return default_server_names()


# ---------------------------------------------------------------------------
# MCP merge & env helpers (must be before main())
# ---------------------------------------------------------------------------
def merge_mcp_servers(path: Path, servers: dict, force: bool = False) -> list:
    """Merge MCP servers into the file's MCP map (fail-closed + backup)."""
    if path.exists():
        original_text = path.read_text(encoding="utf-8", errors="replace")
        data, fmt = load_file(path)
        # Fail closed: existing but unparsable config must not be clobbered
        if not data and original_text.strip():
            backup = path.with_name(path.name + ".bak-arwaky")
            backup.write_text(original_text, encoding="utf-8")
            if not force:
                raise ValueError(
                    f"Refusing to merge into unparsable config file: {path}. "
                    f"Backup saved to {backup}. Use --force only after manual review."
                )
            data, fmt = {}, "json"
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
        data, fmt = {}, "json"

    mcp, mcp_key = get_mcp_map(data)
    if mcp is None:
        if isinstance(data, dict):
            key = "mcp_servers" if fmt == "toml" else "mcpServers"
            data[key] = {}
            mcp = data[key]
            mcp_key = key
        else:
            return []

    merged = []
    for name, srv in servers.items():
        if force or name not in mcp:
            mcp[name] = srv
            merged.append(name)

    if merged and not save_file(path, data, fmt):
        raise RuntimeError(f"Failed to write MCP config: {path}")
    return merged


def set_env_keys(path: Path, pairs: dict) -> None:
    """Set KEY=VALUE lines in a .env file (create if missing)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    for key, val in pairs.items():
        escaped = val.replace('"', '\\"')
        pattern = re.compile(rf"^{re.escape(key)}=")
        replaced = False
        for idx, line in enumerate(lines):
            if pattern.match(line.strip()):
                lines[idx] = f'{key}="{escaped}"'
                replaced = True
                break
        if not replaced:
            lines.append(f'{key}="{escaped}"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

class ConfigWriter(IConfigWriter):
    """Module-level I/O bound to the IConfigWriter contract."""

    def load_file(self, path: Path) -> tuple[dict, str]:
        return load_file(path)

    def save_file(self, path: Path, data: dict, fmt: str | None = None) -> bool:
        if fmt is None:
            fmt = detect_format(path)
        return save_file(path, data, fmt)

    def detect_format(self, path: Path) -> str:
        return detect_format(path)


class ConfigModifier(IConfigModifier):
    """Module-level I/O bound to the IConfigModifier contract."""

    def remove_mcp_servers(self, path: Path, servers: list[str], dry_run: bool = False) -> list[str]:
        return remove_mcp_servers(path, servers, dry_run)

    def remove_env_keys(self, path: Path, keys: list[str], dry_run: bool = False) -> list[str]:
        return remove_env_keys(path, keys, dry_run)

    def list_mcp_servers(self, path: Path) -> list[str]:
        return list_mcp_servers(path)

    def merge_mcp_servers(self, path: Path, servers: dict, force: bool = False) -> list[str]:
        return merge_mcp_servers(path, servers, force)

    def set_env_keys(self, path: Path, pairs: dict) -> None:
        set_env_keys(path, pairs)
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


# ---------------------------------------------------------------------------
# Adapter classes (3-block structure: config -> behavior -> implementation)
# ---------------------------------------------------------------------------
