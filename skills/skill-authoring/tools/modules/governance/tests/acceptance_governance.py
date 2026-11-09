"""Acceptance tests for modules/governance — map 1:1 to the FRD requirement ids.

Each test anchors one `FR-GOVERNANCE-NNN` requirement in `FRD.md`.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from shared.src.design.taxonomy_skills_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
)
from shared.src.design.taxonomy_skills_response import SkillsExitCode


def _make_agent(pack: Path):
    from governance.agent_governance_orchestrator import SkillsGovernanceAgent
    from governance.capabilities_skills_locker import SkillsLocker
    from governance.capabilities_skills_mover import SkillsMover
    from governance.capabilities_skills_piner import SkillsPiner

    return SkillsGovernanceAgent(
        locker=SkillsLocker(),
        piner=SkillsPiner(),
        mover=SkillsMover(),
        default_root=str(pack),
    )


def test_fr_governance_001_lock_unlock_toggles_the_sidecar_flag():
    """AC-GOVERNANCE-001: FR-GOVERNANCE-001 — a lock/unlock pair
    returns the sidecar to its original state."""
    with tempfile.TemporaryDirectory() as d:
        pack = Path(d) / "cats"
        skill_dir = pack / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\n---\n")

        agent = _make_agent(pack)
        agent.execute(SkillsRequest(op=SkillsOp.LOCK, query=SkillQuery("my-skill")))
        record = json.loads((skill_dir / ".usage.json").read_text())
        assert record.get("locked") is True

        agent.execute(SkillsRequest(op=SkillsOp.UNLOCK, query=SkillQuery("my-skill")))
        record = json.loads((skill_dir / ".usage.json").read_text())
        assert record.get("locked") is False


def test_fr_governance_002_pin_unpin_toggles_the_sidecar_flag():
    """AC-GOVERNANCE-002: FR-GOVERNANCE-002 — a pin/unpin pair
    returns the sidecar to its original state."""
    with tempfile.TemporaryDirectory() as d:
        pack = Path(d) / "cats"
        skill_dir = pack / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\n---\n")

        agent = _make_agent(pack)
        agent.execute(SkillsRequest(op=SkillsOp.PIN, query=SkillQuery("my-skill")))
        record = json.loads((skill_dir / ".usage.json").read_text())
        assert record.get("pinned") is True

        agent.execute(SkillsRequest(op=SkillsOp.UNPIN, query=SkillQuery("my-skill")))
        record = json.loads((skill_dir / ".usage.json").read_text())
        assert record.get("pinned") is False


def test_fr_governance_003_move_rehomes_the_skill_inside_the_pack_root():
    """AC-GOVERNANCE-003: FR-GOVERNANCE-003 — a move into an existing
    target category re-homes the skill directory under the pack root."""
    with tempfile.TemporaryDirectory() as d:
        pack = Path(d)
        skill_dir = pack / "cats" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\n---\n")
        (pack / "dogs").mkdir()

        agent = _make_agent(pack)
        result = agent.execute(
            SkillsRequest(
                op=SkillsOp.MOVE,
                query=SkillQuery("my-skill"),
                flags={"target": "dogs"},
                apply=True,
            )
        )
        assert result.ok is True
        assert (pack / "dogs" / "my-skill").is_dir()


def test_fr_governance_003_missing_target_flag_is_a_usage_error():
    """AC-GOVERNANCE-004: FR-GOVERNANCE-003 edge case — a MOVE request
    without a `--target` flag surfaces a usage error."""
    with tempfile.TemporaryDirectory() as d:
        pack = Path(d)
        skill_dir = pack / "cats" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\n---\n")

        agent = _make_agent(pack)
        result = agent.execute(
            SkillsRequest(op=SkillsOp.MOVE, query=SkillQuery("my-skill"))
        )
        assert result.ok is False
        assert result.exit_code == SkillsExitCode.USAGE_ERROR
