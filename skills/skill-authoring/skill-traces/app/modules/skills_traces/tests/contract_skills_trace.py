"""Contract tests — verify the response envelope contract and opcode registration."""
from __future__ import annotations

from shared.src.skills_traces.taxonomy_skills_request import SkillsOp
from shared.src.skills_traces.taxonomy_skills_response import (
    SkillsExitCode,
    SkillsResult,
)


def test_contract_trace_op_registered() -> None:
    """CT-TRACE-001: SkillsOp.TRACES is registered."""
    assert SkillsOp.TRACES.value == "traces"


def test_contract_exit_codes() -> None:
    """CT-TRACE-002: exit codes are the documented 0/1/2/3 set."""
    assert SkillsExitCode.CLEAN == 0
    assert SkillsExitCode.ISSUES_FOUND == 1
    assert SkillsExitCode.USAGE_ERROR == 2
    assert SkillsExitCode.CATALOG_DRIFT == 3


def test_contract_result_defaults() -> None:
    """CT-TRACE-003: SkillsResult defaults carry safe zero state."""
    result = SkillsResult(ok=False)
    assert result.ok is False
    assert result.op == SkillsOp.LIST
    assert result.exit_code == 0


def test_contract_result_can_hold_trace_fields() -> None:
    """CT-TRACE-004: SkillsResult can hold usage, phrases, state fields."""
    result = SkillsResult(ok=True, op=SkillsOp.TRACES)
    assert result.usage is None
    assert result.phrases is None
    assert result.state is None
    assert result.state_status is None
    assert result.collect_summary is None
