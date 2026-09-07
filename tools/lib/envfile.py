"""Helper baca/tulis .env files (Python)."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable


def parse_env_file(path: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
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
        val = val.strip().strip('"').strip("'")
        if key:
            env[key] = val
    return env


def load_first_env(candidates: Iterable[Path]) -> Dict[str, str]:
    for candidate in candidates:
        c = Path(candidate)
        if c.exists():
            return parse_env_file(c)
    return {}


def update_env_file(path: Path, key: str, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    if path.exists():
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            lines = []
    found = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key}="):
            new_lines.append(f'{key}="{value}"')
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f'{key}="{value}"')
    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def remove_env_keys(path: Path, keys: Iterable[str]) -> list:
    """Remove KEY=... lines. Returns removed keys."""
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
