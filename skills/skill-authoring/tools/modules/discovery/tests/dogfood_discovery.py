"""Dogfood test: drive the discovery agent through the real CLI entry path.

Dogfood tests skip when the CLI entry point is unavailable, per the
AES103 `dogfood_` coverage role.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_TOOLS_ROOT = Path(__file__).resolve().parents[2]
for _ns in (
    _TOOLS_ROOT,
    _TOOLS_ROOT / "shared" / "src",
    _TOOLS_ROOT / "discovery" / "src",
):
    if _ns.is_dir() and str(_ns) not in sys.path:
        sys.path.insert(0, str(_ns))


def test_cli_discover_subcommand(tmp_path):
    """DOG-DISCOVERY-001: `sac skills discover` returns JSON rows."""
    cat_dir = tmp_path / "automation" / "fetch"
    cat_dir.mkdir(parents=True)
    (cat_dir / "SKILL.md").write_text(
        "---\nname: fetch\ndescription: Fetch web content to markdown.\n"
        "---\n# Fetch\n",
        encoding="utf-8",
    )

    entry = _TOOLS_ROOT / "root_cli_entry.py"
    if not entry.exists():
        pytest.skip("root_cli_entry.py not on this tree; no live CLI to dogfood")
    try:
        import root_skills_container  # noqa: F401
    except ModuleNotFoundError:  # pragma: no cover - requires whole app wired
        pytest.skip("root_skills_container cannot import discovery capability; CLI entry not functional")

    proc = subprocess.run(
        [sys.executable, str(entry), "skills", "discover",
         "--skills-root", str(tmp_path), "fetch", "--json"],
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "fetch" in proc.stdout
