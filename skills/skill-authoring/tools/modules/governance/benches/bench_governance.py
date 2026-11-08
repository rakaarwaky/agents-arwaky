"""Benchmarks for modules/governance — performance characteristics.

Run from the repo root:

    python skills/skill-authoring/tools/modules/governance/benches/bench_governance.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

# Make the module tree importable when this file is run as a script.
# The bench lives at modules/governance/benches/bench_governance.py, so
# parents[2] = modules/ (the top of the namespace that the conftest
# puts on sys.path for pytest runs of this tree).
_MOD_ROOT = Path(__file__).resolve().parents[2]
if str(_MOD_ROOT) not in sys.path:
    sys.path.insert(0, str(_MOD_ROOT))


def bench_agent_construction():
    """Benchmark: construct the governance agent with mocked capabilities."""
    from governance.agent_governance_orchestrator import SkillsGovernanceAgent

    iterations = 1000
    start = time.perf_counter()
    for _ in range(iterations):
        SkillsGovernanceAgent(
            locker=MagicMock(), piner=MagicMock(), mover=MagicMock()
        )
    elapsed = time.perf_counter() - start
    print(f"Agent construction x{iterations}: {elapsed:.4f}s")
    return elapsed


def bench_agent_execute_dispatch():
    """Benchmark: execute() dispatch overhead for a governance op."""
    from governance.agent_governance_orchestrator import SkillsGovernanceAgent
    from shared.src.design.taxonomy_skills_request import (
        SkillQuery,
        SkillsOp,
        SkillsRequest,
    )

    agent = SkillsGovernanceAgent(
        locker=MagicMock(), piner=MagicMock(), mover=MagicMock()
    )
    iterations = 1000
    start = time.perf_counter()
    for _ in range(iterations):
        agent.execute(SkillsRequest(op=SkillsOp.PIN, query=SkillQuery("skill-a")))
    elapsed = time.perf_counter() - start
    print(f"Execute dispatch x{iterations}: {elapsed:.4f}s")
    return elapsed


def bench_capability_instantiation():
    """Benchmark: instantiate all governance capabilities."""
    from governance.capabilities_skills_locker import SkillsLocker
    from governance.capabilities_skills_mover import SkillsMover
    from governance.capabilities_skills_piner import SkillsPiner

    iterations = 1000
    start = time.perf_counter()
    for _ in range(iterations):
        SkillsLocker()
        SkillsPiner()
        SkillsMover()
    elapsed = time.perf_counter() - start
    print(f"Capability instantiation x{iterations}: {elapsed:.4f}s")
    return elapsed


if __name__ == "__main__":
    print("=" * 60)
    print("Governance Module Benchmarks")
    print("=" * 60)
    bench_agent_construction()
    bench_agent_execute_dispatch()
    bench_capability_instantiation()
    print("=" * 60)
