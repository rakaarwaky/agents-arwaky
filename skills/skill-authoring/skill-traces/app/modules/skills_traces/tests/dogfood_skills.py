"""Dogfood tests — runs against the live GROK_HOME trace state."""
from __future__ import annotations

import pytest


@pytest.mark.dogfood
def test_dogfood_trace_state_protocol_is_satisfied():
    """DOG-TRACE-001: SkillsTracesState satisfies its protocol."""
    from shared.src.skills_traces.contract_skills_protocol import (
        ISkillsTraceStateProtocol,
    )

    from skills_traces.src.capabilities_skills_state import SkillsTracesState

    assert isinstance(SkillsTracesState(), ISkillsTraceStateProtocol)


@pytest.mark.dogfood
def test_dogfood_trace_scan_protocol_is_satisfied():
    """DOG-TRACE-002: SkillsTracesScan satisfies its protocol."""
    from shared.src.skills_traces.contract_skills_protocol import (
        ISkillsTraceScanProtocol,
    )

    from skills_traces.src.capabilities_skills_scan import SkillsTracesScan

    assert isinstance(SkillsTracesScan(), ISkillsTraceScanProtocol)
