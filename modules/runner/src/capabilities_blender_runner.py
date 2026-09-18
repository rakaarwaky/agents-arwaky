"""BlenderRunner — per-tool runner capability (delegates discovery/execution to RunnerBase)."""
from __future__ import annotations

from modules.runner.src.utility_runner_base import RunnerBase


class BlenderRunner(RunnerBase):
    """Per-tool runner capability for blender; inherits RunnerBase behaviour."""
