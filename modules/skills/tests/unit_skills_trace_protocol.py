"""Unit tests for the trace-pipeline contract protocols and taxonomy VOs."""

from __future__ import annotations

import typing

import pytest

from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsListerProtocol,
    ISkillsTracesProtocol,
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
    """The TRACES op is registered on SkillsOp."""
    assert SkillsOp.TRACES.value == "traces"


def test_skills_ops_are_registered() -> None:
    """Every CLI subcommand op is registered on SkillsOp."""
    assert SkillsOp.LIST.value == "list"
    assert SkillsOp.READ.value == "read"
    assert SkillsOp.LINT.value == "lint"
    assert SkillsOp.CATALOG.value == "catalog"
    assert SkillsOp.DISCOVER.value == "discover"
    assert SkillsOp.MOVE.value == "move"
    assert SkillsOp.ARCHIVE.value == "archive"
    assert SkillsOp.CREATE.value == "create"
    assert SkillsOp.TRACES.value == "traces"


def test_trace_state_status_values() -> None:
    """The status flow enum is complete and ordered."""
    assert [s.value for s in TraceStateStatus] == [
        "collected",
        "running",
        "report_ready",
        "curating",
        "done",
        "phase_stall",
        "report_stall",
        "deadline",
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
    """ISkillsTracesProtocol is an ABC: instantiating without methods raises."""
    with pytest.raises(TypeError):
        ISkillsTracesProtocol()  # type: ignore[abstract]
    assert "scan_sessions" in ISkillsTracesProtocol.__abstractmethods__


def test_lister_protocol_gains_json_list_method() -> None:
    """ISkillsListerProtocol carries the global-skill JSON list seam."""
    assert callable(ISkillsListerProtocol.list_skills_json)
    assert "list_skills" in ISkillsListerProtocol.__abstractmethods__
    assert "list_skills_json" not in ISkillsListerProtocol.__abstractmethods__


def test_report_hints_resolve_at_runtime() -> None:
    """The guarded annotations resolve: get_type_hints works on both report VOs."""
    assert typing.get_type_hints(UsageReport)["items"]
    assert typing.get_type_hints(PhrasesReport)["exact_prompts"]
