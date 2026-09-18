"""Version helpers — taxonomy layer (pure functions, allowed in _vo files)."""
from __future__ import annotations

import re
from pathlib import Path

from modules.shared.src.taxonomy_paths_constant import REPO_ROOT as repo_root

from modules.shared.src.taxonomy_version_constant import DEFAULT_VERSION

def _version_file() -> Path:
    return repo_root / "config" / "version.txt"


def read_version() -> str:
    """Current version from config/version.txt (default 0.1.0)."""
    version_file = _version_file()
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return DEFAULT_VERSION


def bump(current: str, part: str) -> str:
    """Bump the current version by *part* (``major``/``minor``/``patch``).

    Raises:
        ValueError: if the version is unparseable or *part* is unknown.
    """
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", current.strip())
    if not m:
        raise ValueError(f"Unrecognized version format: {current!r}")
    major, minor, patch = (int(g) for g in m.groups())
    if part == "major":
        major, minor, patch = major + 1, 0, 0
    elif part == "minor":
        minor, patch = minor + 1, 0
    elif part == "patch":
        patch += 1
    else:
        raise ValueError(
            f"Unknown version part {part!r}; expected major, minor or patch "
            f"(current: {current})"
        )
    return f"{major}.{minor}.{patch}"
