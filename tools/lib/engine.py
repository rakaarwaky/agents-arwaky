#!/usr/bin/env python3
"""agents-arwaky config engine (Python).

Shared library for reading/writing agent harness configuration files:
JSON, JSONC (with // comments) and YAML — with format auto-detection,
comment preservation (YAML via ruamel when available), and helpers for
removing agents-arwaky MCP servers / env keys.

Usage from bash:
    python3 tools/py/engine.py remove-mcp-servers <file> <server1> [server2...]
    python3 tools/py/engine.py remove-env-keys  <file> <key1> [key2...]
    python3 tools/py/engine.py list-mcp-servers <file>
    python3 tools/py/engine.py --help
"""
import json
import os
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Format detection & generic load/dump
# ---------------------------------------------------------------------------
def detect_format(path: Path) -> str:
    name = path.name.lower()
    if name.endswith((".yaml", ".yml")):
        return "yaml"
    if name.endswith(".jsonc"):
        return "jsonc"
    if name.endswith((".json", ".bak")):
        return "json"
    # Fallback: peek content
    try:
        text = path.read_text(encoding="utf-8", errors="replace")[:4096]
        if re.search(r"^\s*[-\w]+\s*:", text, re.MULTILINE):
            return "yaml"
    except OSError:
        pass
    return "json"


def _strip_jsonc_comments(text: str) -> str:
    """Best-effort JSONC -> JSON (strip // and /* */ comments outside strings)."""
    out = []
    i = 0
    n = len(text)
    in_str = False
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if in_str:
            out.append(c)
            if c == "\\":
                out.append(nxt)
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        if c == "/" and nxt == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "/" and nxt == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def load_file(path: Path):
    """Load JSON / JSONC / YAML into a dict. Returns ({}, fmt) on failure."""
    fmt = detect_format(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    if fmt in ("json", "jsonc"):
        if fmt == "jsonc":
            text = _strip_jsonc_comments(text)
        try:
            return json.loads(text), fmt
        except json.JSONDecodeError:
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
            # Best-effort: pertahankan komentar JSONC asli di luar blok yang diubah.
            # Jika file asli ada, simpan komentar baris (//) yang berada di luar bagian mcp/mcpServers.
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
                import yaml
                with path.open("w", encoding="utf-8") as f:
                    yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
        return True
    except (OSError, TypeError, ValueError, ImportError):
        return False


# ---------------------------------------------------------------------------
# MCP server helpers
# ---------------------------------------------------------------------------
def get_mcp_map(data: dict):
    """Return the dict holding MCP servers (mcpServers or mcp)."""
    if isinstance(data, dict):
        if isinstance(data.get("mcpServers"), dict):
            return data["mcpServers"], "mcpServers"
        if isinstance(data.get("mcp"), dict):
            return data["mcp"], "mcp"
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
    """Remove `KEY=...` lines from a .env-style file. Returns removed keys."""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    removed = []
    lines = text.splitlines()
    kept = []
    for line in lines:
        stripped = line.strip()
        hit = False
        for k in keys:
            if stripped.startswith(k + "="):
                hit = True
                removed.append(k)
                break
        if not hit:
            kept.append(line)
    if removed and not dry_run:
        new_text = "\n".join(kept)
        if new_text.strip():
            path.write_text(new_text + "\n", encoding="utf-8")
        else:
            path.unlink(missing_ok=True)
    return removed


# ---------------------------------------------------------------------------
# agents-arwaky server list (single source of truth)
# ---------------------------------------------------------------------------
def default_server_names() -> list:
    """Server names generated by tools/mcp/generate-config.sh (static fallback)."""
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
# CLI entrypoint
# ---------------------------------------------------------------------------

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

    mcp, _ = get_mcp_map(data)
    if mcp is None:
        if isinstance(data, dict):
            data["mcpServers"] = {}
            key = "mcpServers"
        else:
            return []
        mcp = data[key]

    merged = []
    for name, srv in servers.items():
        if force or name not in mcp:
            mcp[name] = srv
            merged.append(name)

    if merged:
        save_file(path, data, fmt)
    return merged


def set_env_keys(path: Path, pairs: dict) -> None:
    """Set KEY=VALUE lines in a .env file (create if missing)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    for key, val in pairs.items():
        pattern = re.compile(rf"^{re.escape(key)}=")
        replaced = False
        for idx, line in enumerate(lines):
            if pattern.match(line.strip()):
                lines[idx] = f'{key}="{val}"'
                replaced = True
                break
        if not replaced:
            lines.append(f'{key}="{val}"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
