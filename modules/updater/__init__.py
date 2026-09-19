"""Updater feature — two business-action capabilities + per-tool leaf adapters.

Capabilities: `capabilities_updater_bumper.py` (FR-001) and
`capabilities_updater_recorder.py` (FR-002). Per-tool update mechanics live in
stateless leaf adapters (`utility_<tool>_updater.py`), one per manifest id,
keyed on the manifest `id`. The orchestrator drives bumper then recorder.
"""
from modules.updater.src.agent_updater_orchestrator import UpdaterOrchestrator

__all__ = ["UpdaterOrchestrator"]
