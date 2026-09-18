"""Sync runner capability — 1:1 verbatim port of tools/sync/sync_all.py.

One-shot 4-step ecosystem sync. The original script body is preserved
verbatim; only imports were swapped to the AES shared modules:
  tools/lib/paths.repo_root -> modules.shared.src.paths.utility_paths
  tools/lib/ui (info/ok/warn) -> modules.shared.src.logging.utility_logging

The original Step 2 executed the deleted ``tools/mcp/generate_config.py``;
per the restore rules it now routes through the AES CLI entry
(``python3 -m modules.cli.src.root_cli_entry mcp generate``) which
delegates to the AES mcp module — equivalent behavior (stdout, exit code),
no flags to pass through.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from modules.shared.src.logging.utility_logging import info, ok, warn
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.sync.contract_sync_protocol import ISyncRunner


ROOT = repo_root()


def run(cmd):
    return subprocess.run(cmd, check=False).returncode  # noqa: S603


def _aa(*args):
    """Run the AES CLI entry in-process as a subprocess (equivalent to 'aa')."""
    return [sys.executable, "-m", "modules.cli.src.root_cli_entry", *args]


def main(argv):
    no_connect = "--no-connect" in argv
    no_update = "--no-update" in argv
    info("Running one-shot ecosystem sync...")

    failures = []
    completed_steps = []
    skipped_steps = []

    if no_update:
        skipped_steps.append("update")
    else:
        info("Step 1: updating tools (pull + reinstall)...")
        if run(_aa("update", "all", "--yes")) != 0:
            failures.append("update")
        else:
            completed_steps.append("update")

    info("Step 2: generating MCP config...")
    if run(_aa("mcp", "generate")) != 0:
        failures.append("mcp-generate")
    else:
        completed_steps.append("mcp-generate")

    if no_connect:
        skipped_steps.append("connect")
    else:
        info("Step 3: reconnecting harnesses...")
        if run(_aa("connect", "--all")) != 0:
            failures.append("connect")
        else:
            completed_steps.append("connect")

    info("Step 4: verifying...")
    if run(_aa("check")) != 0:
        failures.append("check")
    else:
        completed_steps.append("check")

    if failures:
        warn(f"Sync finished with failures: {', '.join(failures)}")
        warn("Completed steps that may need rollback:")
        reversibility = {
            "update": "(reversible: re-run 'aa tool update all')",
            "mcp-generate": "(reversible: rm mcp_servers.generated.json)",
            "connect": "(reversible: aa disconnect --all)",
            "check": "(no action needed)",
        }
        for s in completed_steps:
            warn(f"  - {s} {reversibility.get(s, '')}")
        if skipped_steps:
            warn(f"Skipped by flag (no rollback needed): {', '.join(skipped_steps)}")
        warn("To regenerate MCP: aa mcp generate")
        warn("To reconnect harnesses: aa connect --all")
        return 1

    ok("Ecosystem sync complete.")
    return 0


class SyncRunner(ISyncRunner):
    """One-shot 4-step ecosystem sync: update, mcp generate, connect, check.

    The module-level :func:`main` above is the verbatim original body; this
    class adapts it to the capability contract.

    # Block 1: Configuration (entry-point resolution)
    # Block 2: Step execution
    # Block 3: Failure reporting
    """

    # -- Block 1: Configuration ---------------------------------------------------
    def __init__(self) -> None:
        self._root = repo_root()

    # -- Block 2 / 3: step execution + failure reporting ---------------------------
    def run(self, no_connect: bool, no_update: bool) -> int:
        """Run the 4-step sync; on failure print rollback hints per completed step."""
        return main([f"--{name}" for name, flag in (("no-connect", no_connect), ("no-update", no_update)) if flag])
