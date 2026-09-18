"""Context7Runner — per-tool runner capability (delegates discovery/execution to RunnerBase)."""
from __future__ import annotations

from modules.runner.src.utility_runner_base import RunnerBase


class Context7Runner(RunnerBase):
    """Per-tool runner capability for context7; inherits RunnerBase behaviour."""
