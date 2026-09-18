"""LintRunner — per-tool runner capability (delegates discovery/execution to RunnerBase)."""
from __future__ import annotations

from modules.runner.src.utility_runner_base import RunnerBase


class LintRunner(RunnerBase):
    """Per-tool runner capability for lint; inherits RunnerBase behaviour."""
