"""Config engine pure I/O helpers (utility layer).

Shared by the config capability and the harness capabilities (AES201:
capabilities must not import other capabilities — utility is allowed).
"""
from __future__ import annotations

import json
import re
import tomllib
from collections.abc import Iterable
from pathlib import Path


# ---------------------------------------------------------------------------
# Inlined JSONC stripping (formerly utility_jsonc_parser.strip_jsonc_comments)
# ---------------------------------------------------------------------------
def strip_jsonc_comments(text: str) -> str:
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


# ---------------------------------------------------------------------------
# Inlined TOML writing (formerly utility_toml_write)
# ---------------------------------------------------------------------------
def _toml_write_value(val) -> str:
    """Convert a Python value to its TOML representation."""
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, int) and not isinstance(val, bool):
        return str(val)
    if isinstance(val, float):
        return str(val)
    if isinstance(val, str):
        escaped = val.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(val, list):
        if not val:
            return "[]"
        items = [_toml_write_value(v) for v in val]
        return "[" + ", ".join(items) + "]"
    if isinstance(val, dict):
        if not val:
            return "{}"
        parts = []
        for k, v in val.items():
            parts.append(f"{_toml_quote_key(k)} = {_toml_write_value(v)}")
        return "{ " + ", ".join(parts) + " }"
    return str(val)


def _toml_quote_key(key) -> str:
    """Quote a TOML key only when it contains non-alphanumeric characters."""
    if key and all(c.isalnum() or c in ('-', '_') for c in key):
        return key
    escaped = key.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'


def _toml_section(parts) -> str:
    """Join *parts* into a dotted TOML table path."""
    return ".".join(_toml_quote_key(p) for p in parts)


def _toml_write_table(data, parts=()):
    """Recursively write TOML sections."""
    lines = []
    for key, val in data.items():
        if isinstance(val, list) and val and all(isinstance(i, dict) for i in val):
            continue
        if not isinstance(val, dict):
            lines.append(f"{_toml_quote_key(key)} = {_toml_write_value(val)}")
    for key, val in data.items():
        if not isinstance(val, dict) and not (isinstance(val, list) and val and all(isinstance(i, dict) for i in val)):
            continue
        cur = parts + (key,)
        if isinstance(val, list) and val and all(isinstance(i, dict) for i in val):
            for item in val:
                lines.append("")
                lines.append(f"[[{_toml_section(cur)}]]")
                for ik, iv in item.items():
                    lines.append(f"{_toml_quote_key(ik)} = {_toml_write_value(iv)}")
        elif val and all(isinstance(v, dict) for v in val.values()):
            sub = _toml_write_table(val, cur)
            lines.extend(sub)
        else:
            sub = _toml_write_table(val, cur)
            if sub:
                lines.append("")
                lines.append("[" + _toml_section(cur) + "]")
                lines.extend(sub)
    return lines


def write_toml(data) -> str:
    """Render a dict as a TOML string."""
    lines = _toml_write_table(data)
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Inlined env-file parsing (formerly utility_envfile_parser)
# ---------------------------------------------------------------------------
def _parse_env_file(path: Path) -> dict[str, str]:
    """Parse a .env-style file (KEY=VALUE lines) into a dict."""
    env: dict[str, str] = {}
    if not path.exists():
        return env
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return env
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
            val = val[1:-1].replace('\\"', '"')
        elif len(val) >= 2 and val[0] == "'" and val[-1] == "'":
            val = val[1:-1]
        if key:
            env[key] = val
    return env


def _env_remove_keys(path: Path, keys: Iterable[str]) -> list:
    """Remove KEY=... lines from a .env file. Returns removed keys."""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    keyset = set(keys)
    removed = []
    kept = []
    for line in text.splitlines():
        stripped = line.strip()
        hit = None
        for k in keyset:
            if stripped.startswith(k + "="):
                hit = k
                break
        if hit:
            removed.append(hit)
        else:
            kept.append(line)
    if removed:
        new_text = "\n".join(kept)
        if new_text.strip():
            path.write_text(new_text + "\n", encoding="utf-8")
        else:
            path.unlink(missing_ok=True)
    return removed


def detect_format(path: Path) -> str:
    """Heuristic guess for the config format from name or content."""
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
        import yaml
        data = yaml.safe_load(text) or {}
    except ImportError:
        data = None  # pyyaml not installed; try ruamel below
    except yaml.YAMLError:
        data = None  # malformed YAML; try ruamel below
    if data is not None:
        return data, fmt
    # ruamel fallback
    try:
        from ruamel import yaml
        data = yaml.YAML(typ="safe").load(text) or {}
        return data, fmt
    except ImportError:
        pass  # ruamel not installed
    except yaml.YAMLError:
        pass  # malformed YAML
    return {}, fmt


def save_file(path: Path, data, fmt: str, preserve_comments: bool = True) -> bool:
    """Write *data* back to *path* preserving its format. Returns True on success."""
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
                    from ruamel import yaml
                    y = yaml.YAML()
                    y.preserve_quotes = True
                    with path.open("w", encoding="utf-8") as f:
                        y.dump(data, f)
                    dumped = True
                except ImportError:
                    dumped = False  # ruamel unavailable; fall back to pyyaml
                except yaml.YAMLError:
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
    """Return the dict holding MCP servers and its canonical key name."""
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
    """List all registered MCP server names in *path*; empty list if absent."""
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
    if dry_run:
        env = _parse_env_file(path)
        return [k for k in keys if k in env]
    return _env_remove_keys(path, keys)


# ---------------------------------------------------------------------------
# agents-arwaky server list (single source of truth)
# ---------------------------------------------------------------------------
def default_server_names() -> list:
    """Server names generated by modules/mcp/src/capabilities_mcp_generator.py (static fallback)."""
    return [
        "context7", "fetch", "anytype", "codegraph",
        "vision-arwaky", "qwen-web-arwaky", "blender-arwaky", "lint-arwaky",
        "workspace", "hindsight",
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

    mcp, _mcp_key = get_mcp_map(data)
    if mcp is None:
        if isinstance(data, dict):
            key = "mcp_servers" if fmt == "toml" else "mcpServers"
            data[key] = {}
            mcp = data[key]
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


__all__ = [
    "arwaky_server_names",
    "default_server_names",
    "detect_format",
    "get_mcp_map",
    "list_mcp_servers",
    "load_file",
    "merge_mcp_servers",
    "remove_env_keys",
    "remove_mcp_servers",
    "save_file",
    "set_env_keys",
]
