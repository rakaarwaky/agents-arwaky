"""VisionRunner — per-tool runner capability (delegates discovery/execution to RunnerBase)."""
from __future__ import annotations

from modules.runner.src.utility_runner_base import RunnerBase


class VisionRunner(RunnerBase):
    """Per-tool runner capability for vision; inherits RunnerBase behaviour."""
