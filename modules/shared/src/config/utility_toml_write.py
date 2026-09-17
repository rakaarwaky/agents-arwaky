"""TOML writing helpers (moved from tools/lib/engine.py, renamed public)."""
from __future__ import annotations


def write_toml_value(val) -> str:
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
        items = [write_toml_value(v) for v in val]
        return "[" + ", ".join(items) + "]"
    if isinstance(val, dict):
        if not val:
            return "{}"
        parts = []
        for k, v in val.items():
            parts.append(f"{quote_key(k)} = {write_toml_value(v)}")
        return "{ " + ", ".join(parts) + " }"
    return str(val)


def quote_key(key) -> str:
    if key and all(c.isalnum() or c in ('-', '_') for c in key):
        return key
    escaped = key.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'


def toml_section(parts) -> str:
    return ".".join(quote_key(p) for p in parts)


def write_toml_table(data, parts=()):
    """Recursively write TOML sections."""
    lines = []
    # Emit simple key-values first
    for key, val in data.items():
        if isinstance(val, list) and val and all(isinstance(i, dict) for i in val):
            continue  # array-of-tables handled below
        if not isinstance(val, dict):
            lines.append(f"{quote_key(key)} = {write_toml_value(val)}")
    # Handle dict values (nested tables)
    for key, val in data.items():
        if not isinstance(val, dict) and not (isinstance(val, list) and val and all(isinstance(i, dict) for i in val)):
            continue
        cur = parts + (key,)
        if isinstance(val, list) and val and all(isinstance(i, dict) for i in val):
            for item in val:
                lines.append("")
                lines.append(f"[[{toml_section(cur)}]]")
                for ik, iv in item.items():
                    lines.append(f"{quote_key(ik)} = {write_toml_value(iv)}")
        elif val and all(isinstance(v, dict) for v in val.values()):
            # Namespace container (all children are sub-sections) - skip its own header
            sub = write_toml_table(val, cur)
            lines.extend(sub)
        else:
            sub = write_toml_table(val, cur)
            if sub:
                lines.append("")
                lines.append("[" + toml_section(cur) + "]")
                lines.extend(sub)
    return lines


def write_toml(data) -> str:
    lines = write_toml_table(data)
    return "\n".join(lines) + "\n"
