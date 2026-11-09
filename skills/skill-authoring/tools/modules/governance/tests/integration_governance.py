"""Integration tests for modules/governance — agent + capability wiring."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from shared.src.design.taxonomy_skills_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
)


def _make_pack(tmp: Path, category: str, skill: str) -> Path:
    skill_dir = tmp / category / skill
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: skill\n---\n")
    return tmp


def test_agent_with_locker_capability_end_to_end():
    """IT-GOVERNANCE-001: agent + real locker toggles the locked sidecar flag."""
    from governance.agent_governance_orchestrator import SkillsGovernanceAgent
    from governance.capabilities_skills_locker import SkillsLocker

    with tempfile.TemporaryDirectory() as d:
        pack = Path(d)
        _make_pack(pack, "cats", "my-skill")
        agent = SkillsGovernanceAgent(locker=SkillsLocker(), default_root=str(pack))
        agent.execute(SkillsRequest(op=SkillsOp.LOCK, query=SkillQuery("my-skill")))
        record = json.loads((pack / "cats" / "my-skill" / ".usage.json").read_text())
        assert record.get("locked") is True, "locker must have set the locked flag"


def test_agent_with_piner_capability_end_to_end():
    """IT-GOVERNANCE-002: agent + real piner toggles the pinned sidecar flag."""
    from governance.agent_governance_orchestrator import SkillsGovernanceAgent
    from governance.capabilities_skills_piner import SkillsPiner

    with tempfile.TemporaryDirectory() as d:
        pack = Path(d)
        _make_pack(pack, "cats", "my-skill")
        agent = SkillsGovernanceAgent(piner=SkillsPiner(), default_root=str(pack))
        agent.execute(SkillsRequest(op=SkillsOp.PIN, query=SkillQuery("my-skill")))
        record = json.loads((pack / "cats" / "my-skill" / ".usage.json").read_text())
        assert record.get("pinned") is True, "piner must have set the pinned flag"


def test_mover_plan_move_is_pure_and_apply_move_writes():
    """IT-GOVERNANCE-003: mover.plan_move is pure, apply_move writes the move."""
    from governance.capabilities_skills_mover import SkillsMover

    with tempfile.TemporaryDirectory() as d:
        pack = Path(d)
        _make_pack(pack, "cats", "my-skill")
        (pack / "dogs").mkdir()
        mover = SkillsMover()
        plan = mover.plan_move("my-skill", "dogs", pack)
        assert plan.kind == "move"
        assert plan.already_in_category is False
        outcome = mover.apply_move(plan)
        assert outcome.message
        assert (pack / "dogs" / "my-skill").is_dir()
        assert not (pack / "cats" / "my-skill").exists()


def test_mover_move_into_same_category_is_a_noop():
    """IT-GOVERNANCE-004: moving a skill into its own category is a no-op plan."""
    from governance.capabilities_skills_mover import SkillsMover

    with tempfile.TemporaryDirectory() as d:
        pack = Path(d)
        _make_pack(pack, "cats", "my-skill")
        mover = SkillsMover()
        plan = mover.plan_move("my-skill", "cats", pack)
        assert plan.already_in_category is True
