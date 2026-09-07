#!/usr/bin/env python3
"""Bump the release version across project manifests.

Updates ``pyproject.toml`` and ``blender_mcp_addon/blender_manifest.toml`` to
the next patch version, rebuilds the addon ZIP, commits, tags, and pushes.

Usage:
    uv run python scripts/build/bump_release_version.py

The script assumes a clean working tree on the default branch with push
permissions configured.
"""

import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
MANIFEST_PATH = PROJECT_ROOT / "blender_mcp_addon" / "blender_manifest.toml"
ADDON_BUILDER = SCRIPT_DIR / "build_addon_package.py"
DIST_ZIP = PROJECT_ROOT / "dist" / "blender_mcp_addon.zip"


def bump_version(current_version: str) -> str:
    """Return the next patch version, falling back to ``.1`` suffix."""
    parts = current_version.split(".")
    if len(parts) == 3:
        try:
            parts[2] = str(int(parts[2]) + 1)
            return ".".join(parts)
        except ValueError:
            pass
    return current_version + ".1"


def run_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a subprocess and surface stderr on failure."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result


def replace_version(path: Path, new_version: str) -> str | None:
    """Replace the first ``version = "..."`` occurrence; return old value."""
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"(.*?)"', content, re.MULTILINE)
    if not match:
        return None
    old_version = match.group(1)
    new_content = re.sub(
        r'^version\s*=\s*".*?"',
        f'version = "{new_version}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )
    path.write_text(new_content, encoding="utf-8")
    return old_version


def main() -> None:
    if not PYPROJECT_PATH.exists():
        print(f"pyproject.toml not found at {PYPROJECT_PATH}")
        sys.exit(1)

    content = PYPROJECT_PATH.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"(.*?)"', content, re.MULTILINE)
    if not match:
        print(f"Could not find version in {PYPROJECT_PATH}")
        sys.exit(1)

    old_version = match.group(1)
    new_version = bump_version(old_version)

    # Bump pyproject.toml
    replace_version(PYPROJECT_PATH, new_version)
    print(f"Bumped pyproject.toml version: {old_version} -> {new_version}")

    # Bump blender_manifest.toml (best-effort)
    manifest_old = replace_version(MANIFEST_PATH, new_version)
    if manifest_old is not None:
        print(f"Bumped blender_manifest.toml version: {manifest_old} -> {new_version}")
        run_command(["git", "add", str(MANIFEST_PATH)])
    elif MANIFEST_PATH.exists():
        print(f"Could not find version in {MANIFEST_PATH}")
    else:
        print(f"{MANIFEST_PATH.name} not found, skipping manifest bump")

    # Build the canonical addon ZIP under dist/ for release workflows
    build_res = run_command([sys.executable, str(ADDON_BUILDER)])
    if build_res.returncode != 0:
        print("Error: Failed to build addon ZIP")
        sys.exit(1)

    if not DIST_ZIP.exists():
        print(f"Warning: Built zip file not found in {DIST_ZIP.parent}")

    # Git commit + tag + push
    run_command(["git", "add", str(PYPROJECT_PATH)])
    status = run_command(["git", "status", "--porcelain"])
    if status.stdout.strip():
        run_command(["git", "commit", "--no-verify", "-m", f"chore: bump version to {new_version}"])
        run_command(["git", "tag", f"v{new_version}"])
        run_command(["git", "push"])
        run_command(["git", "push", "origin", f"v{new_version}"])
    else:
        print("No changes to commit")


if __name__ == "__main__":
    main()
