"""Root composition — runner capability wiring + tool-lifecycle aggregate.

The AES root layer is the only layer allowed to import `capabilities*`;
this module wires the two runner capabilities (discoverer, executor) and
builds the ToolOrchestrator aggregate by composing the installer /
updater / uninstaller roots.

The three sibling roots are imported lazily (inside the method that builds
the aggregate) so that importing `modules.runner` never forces a full
sibling import at module load — this breaks the runner -> installer /
updater / uninstaller -> runner partial-init cycle.
"""
from __future__ import annotations

from modules.runner.src.agent_runner_orchestrator import RunnerOrchestrator, ToolOrchestrator
from modules.runner.src.contract_tool_runner_aggregate import IToolAggregate


def create_runner_feature() -> IToolAggregate:
    """Fully-wired tool feature aggregate.

    Composition-time wiring only: the runner root composes the installer /
    updater / uninstaller roots. Each root's registry is already built by
    its own composition module; here we merely instantiate the orchestrators.
    """
    # Deferred so `import modules.runner` does not import sibling roots at load.
    from modules.installer.src.root_tool_installer_registry import build_installer_registry
    from modules.updater.src.root_tool_updater_registry import build_updater_orchestrator
    from modules.uninstaller.src.root_tool_uninstaller_registry import build_uninstaller_orchestrator

    runner = RunnerOrchestrator()
    installer = build_installer_registry()
    updater = build_updater_orchestrator()
    uninstaller = build_uninstaller_orchestrator()
    return ToolOrchestrator(runner, installer, updater, uninstaller)
