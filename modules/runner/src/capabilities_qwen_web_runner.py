"""QwenWebRunner — per-tool runner capability (delegates discovery/execution to RunnerBase)."""
from __future__ import annotations

from modules.runner.src.utility_runner_base import RunnerBase


class QwenWebRunner(RunnerBase):
    """Per-tool runner capability for qwen-web; inherits RunnerBase behaviour."""
