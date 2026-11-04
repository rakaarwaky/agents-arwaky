"""Integration test: the root CLI skills bootstrap resolves the colocated packages.

Spawns ``python3 -m modules.root_cli_entry skills list`` from the repo root
with PYTHONPATH set to only the repo root, and asserts:
  1. exit code 0 (the skills dispatch reaches the design-side aggregate)
  2. the two namespace roots appear in the child\'s sys.path exactly once
     each (the bootstrap in modules/root_cli_entry.py ran, idempotently)
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_root_cli_skills_bootstrap_and_dispatch() -> None:
    """The sys.path bootstrap in modules/root_cli_entry.py exposes the
    colocated ``skills_design`` / ``skills_traces`` packages and the
    ``skills list`` dispatch completes without error."""
    repo_root = Path(__file__).resolve().parents[3]
    design_ns = str(repo_root / "skills" / "skill-authoring" / "skill-design" / "modules")
    traces_ns = str(repo_root / "skills" / "skill-authoring" / "skill-traces" / "modules")

    probe = (
        "import sys; "
        f"assert sys.path.count({design_ns!r}) == 1, 'design ns must appear exactly once'; "
        f"assert sys.path.count({traces_ns!r}) == 1, 'traces ns must appear exactly once'; "
        "sys.exit(0)"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root)
    # Import modules.root_cli_entry in the child so its module-level bootstrap
    # runs; then verify the two namespace roots are each present exactly once.
    completed = subprocess.run(
        [sys.executable, "-c", "import modules.root_cli_entry; " + probe],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, (
        f"bootstrap probe failed (rc={completed.returncode}):\n"
        f"stderr: {completed.stderr[-500:]}"
    )

    # Now run the actual CLI dispatch.
    completed = subprocess.run(
        [sys.executable, "-m", "modules.root_cli_entry", "skills", "list"],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, (
        f"skills list failed (rc={completed.returncode}):\n"
        f"stdout: {completed.stdout[-300:]}\n"
        f"stderr: {completed.stderr[-500:]}"
    )
    assert "SKILL" in completed.stdout, "skills list did not print the skill table"
