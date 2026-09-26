"""Host process runners — domain-agnostic command execution (utility).

Stateless subprocess helpers shared by daemon and tools capabilities.
"""
from __future__ import annotations

import subprocess


def run_cmd(cmd, **kw):
    """Run *cmd* with check=False; return the CompletedProcess."""
    return subprocess.run(cmd, check=False, **kw)


def cmd_out(cmd, **kw) -> str:
    """Run *cmd*, capture stdout, return stripped text."""
    return subprocess.run(
        cmd, capture_output=True, text=True, check=False, **kw
    ).stdout.strip()


__all__ = ["cmd_out", "run_cmd"]
