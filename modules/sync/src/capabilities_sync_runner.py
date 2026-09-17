"""Sync runner capability — port of sync/sync_all.py."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from modules.shared.src.logging.utility_logging import info, ok, warn
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.sync.contract_sync_protocol import ISyncRunner

#: step -> rollback hint shown when the sync fails
REVERSIBILITY = {
    "update": "(reversible: re-run 'aa tool update all')",
    "mcp-generate": "(reversible: rm mcp_servers.generated.json)",
    "connect": "(reversible: aa disconnect --all)",
    "check": "(no action needed)",
}


class SyncRunner(ISyncRunner):
    """One-shot 4-step ecosystem sync: update, mcp generate, connect, check.

    # Block 1: Configuration (entry-point resolution)
    # Block 2: Step execution
    # Block 3: Failure reporting
    """

    # -- Block 1: Configuration ---------------------------------------------------
    def __init__(self) -> None:
        self._root = repo_root()
        # All steps route through the thin CLI launcher (tools/cli/arwaky.py),
        # which delegates to the AES modules under modules/.
        self._cli = self._root / "tools" / "cli" / "arwaky.py"

    # -- Block 2: Step execution ----------------------------------------------------
    @staticmethod
    def _run(cmd: list[str]) -> int:
        return subprocess.run(cmd, check=False).returncode  # noqa: S603

    def run(self, no_connect: bool, no_update: bool) -> int:
        """Run the 4 steps; on failure print rollback hints per completed step."""
        info("Running one-shot ecosystem sync...")
        failures: list[str] = []
        completed_steps: list[str] = []
        skipped_steps: list[str] = []

        if no_update:
            skipped_steps.append("update")
        else:
            info("Step 1: updating tools (pull + reinstall)...")
            if self._run([sys.executable, str(self._cli), "update", "all", "--yes"]) != 0:
                failures.append("update")
            else:
                completed_steps.append("update")

        info("Step 2: generating MCP config...")
        if self._run([sys.executable, str(self._cli), "mcp", "generate"]) != 0:
            failures.append("mcp-generate")
        else:
            completed_steps.append("mcp-generate")

        if no_connect:
            skipped_steps.append("connect")
        else:
            info("Step 3: reconnecting harnesses...")
            if self._run([sys.executable, str(self._cli), "connect", "--all"]) != 0:
                failures.append("connect")
            else:
                completed_steps.append("connect")

        info("Step 4: verifying...")
        if self._run([sys.executable, str(self._cli), "check"]) != 0:
            failures.append("check")
        else:
            completed_steps.append("check")

        # -- Block 3: Failure reporting -------------------------------------------
        if failures:
            warn(f"Sync finished with failures: {', '.join(failures)}")
            warn("Completed steps that may need rollback:")
            for step in completed_steps:
                warn(f"  - {step} {REVERSIBILITY.get(step, '')}")
            if skipped_steps:
                warn(f"Skipped by flag (no rollback needed): {', '.join(skipped_steps)}")
            warn("To regenerate MCP: aa mcp generate")
            warn("To reconnect harnesses: aa connect --all")
            return 1
        ok("Ecosystem sync complete.")
        return 0
