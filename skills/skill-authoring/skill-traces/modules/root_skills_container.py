"""Skills traces composition root (AES root layer).

Wires every contract, taxonomy, utility, capability, and agent into a
fully-wired ``ISkillsAggregate`` for the traces feature. The root is the
only module that knows all the packages exist and composes them.

Every module it needs lives under this package tree:
  - contracts:   shared/src/skills_traces/contract_skills_*.py
  - taxonomy:    shared/src/skills_traces/taxonomy_skills_*.py
  - utility:     shared/src/skills_traces/utility_skill_pack.py,
                 shared/src/skills_traces/utility_skills_trace_state.py,
                 shared/src/common/taxonomy_skill_vo.py
  - capabilities: skills_traces/src/capabilities_skills_traces.py
  - agent:       skills_traces/src/agent_skills_orchestrator.py

The surface is NOT imported here (no root→surface coupling); the CLI
entry point injects the aggregate into the surface at the call site.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.skills_traces.contract_skills_aggregate import ISkillsAggregate
from shared.src.skills_traces.contract_skills_protocol import ISkillsTracesProtocol
from skills_traces.src.agent_skills_orchestrator import SkillsAgent
from skills_traces.src.capabilities_skills_traces import SkillsTraces


class SkillsContainer:
    """Construct the wired traces feature."""

    def __init__(self, default_root: Path | None = None) -> None:
        self._traces: ISkillsTracesProtocol = SkillsTraces()
        self._agent: ISkillsAggregate = SkillsAgent(
            traces=self._traces, default_root=default_root
        )

    @property
    def aggregate(self) -> ISkillsAggregate:
        """Return the wired SkillsAgent as ISkillsAggregate."""
        return self._agent

    @property
    def traces(self) -> ISkillsTracesProtocol:
        """Return the wired traces capability."""
        return self._traces


def default_aggregate(default_root: Path | None = None) -> ISkillsAggregate:
    """Fully-wired traces feature aggregate."""
    return SkillsContainer(default_root=default_root).aggregate


def default_container(default_root: Path | None = None) -> SkillsContainer:
    """Fully-wired traces feature container."""
    return SkillsContainer(default_root=default_root)


__all__ = ["SkillsContainer", "default_aggregate", "default_container"]
