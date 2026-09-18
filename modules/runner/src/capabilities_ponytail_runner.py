"""PonytailRunner — per-tool runner capability (delegates discovery/execution to RunnerBase)."""
from __future__ import annotations

from modules.runner.src.utility_runner_base import RunnerBase


class PonytailRunner(RunnerBase):
    """Per-tool runner capability for ponytail; inherits RunnerBase behaviour."""
