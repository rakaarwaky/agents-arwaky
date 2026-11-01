"""Unit tests for the trace-pipeline contract protocols and taxonomy VOs."""

from __future__ import annotations

import pytest

from modules.shared.src.skills.contract_skills_protocol import (
    IPhrasesProtocol,
    ISkillsIndexProtocol,
    IStateProtocol,
    ITrackerProtocol,
)
from modules.shared.src.skills.taxonomy_skills_authoring_vo import (
    PhrasesReport,
    UsageReport,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    PhraseRow,
    SkillsOp,
    SkillUsageItem,
    TraceDecision,
    TraceSessionRecord,
    TraceStateStatus,
)


def test_trace_ops_exist() -> None:
    """The four trace ops are registered on SkillsOp."""
    assert SkillsOp.TRACE_COLLECT.value == "trace-collect"
    assert SkillsOp.TRACE_USAGE.value == "trace-usage"
    assert SkillsOp.TRACE_PHRASES.value == "trace-phrases"
    assert SkillsOp.TRACE_STATE.value == "trace-state"


def test_trace_state_status_values() -> None:
    """The status flow enum is complete and ordered."""
    assert [s.value for s in TraceStateStatus] == [
        "collected",
        "running",
        "report_ready",
        "curating",
        "done",
    ]


def test_trace_vos_are_frozen() -> None:
    """The new taxonomy VOs are frozen dataclasses."""
    record = TraceSessionRecord(id="s1", index=0, cwd="/w")
    item = SkillUsageItem(name="lint", source="repo", path="/skills/lint", loaded=True)
    row = PhraseRow(phrase="fix the ci please", sessions=2, occurrences=3)
    decision = TraceDecision(
        date="2026-11-01",
        run_dir="/run",
        decision_id="A3",
        kind="skill",
        action="delete",
        target="old-skill",
        target_path="/skills/old-skill",
        decision="applied",
    )
    with pytest.raises(AttributeError):
        record.id = "s2"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        item.count = 9  # type: ignore[union-attr]
    with pytest.raises(AttributeError):
        row.sessions = 1  # type: ignore[union-attr]
    with pytest.raises(AttributeError):
        decision.decision = "rejected"  # type: ignore[union-attr]


def test_report_vos_are_frozen() -> None:
    """UsageReport and PhrasesReport are frozen dataclasses."""
    usage = UsageReport(kept_sessions=1, items=(SkillUsageItem(name="a", source="repo", path="/a", loaded=True),), unused_loaded=("a",))
    phrases = PhrasesReport(exact_prompts=(PhraseRow(phrase="p", sessions=2, occurrences=2),), repeated_instruction_lines=())
    with pytest.raises(AttributeError):
        usage.kept_sessions = 5  # type: ignore[union-attr]
    with pytest.raises(AttributeError):
        phrases.exact_prompts = ()  # type: ignore[union-attr]


def test_trace_protocols_are_abstract() -> None:
    """The three new protocols are ABCs: instantiating without methods raises."""
    with pytest.raises(TypeError):
        ITrackerProtocol()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IPhrasesProtocol()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IStateProtocol()  # type: ignore[abstract]


def test_index_protocol_gains_json_list_method() -> None:
    """ISkillsIndexProtocol now carries the global-skill JSON list seam."""
    assert callable(ISkillsIndexProtocol.list_skills_json)
    assert "list_skills" in ISkillsIndexProtocol.__abstractmethods__
    assert "list_skills_json" not in ISkillsIndexProtocol.__abstractmethods__
