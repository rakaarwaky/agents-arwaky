"""Contract tests for modules/governance — capability protocol implementations."""
from __future__ import annotations


def test_locker_protocol_contract_methods_exist():
    """CP-GOVERNANCE-005: the locker protocol declares lock/unlock."""
    from shared.src.design.contract_skills_protocol import ISkillsLockerProtocol

    assert hasattr(ISkillsLockerProtocol, "lock")
    assert hasattr(ISkillsLockerProtocol, "unlock")


def test_piner_protocol_contract_methods_exist():
    """CP-GOVERNANCE-006: the piner protocol declares pin/unpin."""
    from shared.src.design.contract_skills_protocol import ISkillsPinerProtocol

    assert hasattr(ISkillsPinerProtocol, "pin")
    assert hasattr(ISkillsPinerProtocol, "unpin")


def test_mover_protocol_contract_methods_exist():
    """CP-GOVERNANCE-007: the mover protocol declares plan_move/apply_move."""
    from shared.src.design.contract_skills_protocol import ISkillsMoverProtocol

    assert hasattr(ISkillsMoverProtocol, "plan_move")
    assert hasattr(ISkillsMoverProtocol, "apply_move")
