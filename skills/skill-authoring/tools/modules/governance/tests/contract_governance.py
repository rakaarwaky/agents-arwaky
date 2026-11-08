"""Contract tests for modules/governance — protocol implementations exist."""
from __future__ import annotations


def test_protocol_classes_exist():
    """CP-GOVERNANCE-001: the three governance protocol classes exist and are ABCs."""
    from shared.src.design.contract_skills_protocol import (
        ISkillsLockerProtocol,
        ISkillsMoverProtocol,
        ISkillsPinerProtocol,
    )

    for protocol in (
        ISkillsLockerProtocol,
        ISkillsMoverProtocol,
        ISkillsPinerProtocol,
    ):
        assert protocol.__abstractmethods__, (
            f"{protocol.__name__} declares no methods"
        )


def test_aggregate_contract_is_abstract():
    """CP-GOVERNANCE-002: the governance aggregate contract stays an ABC."""
    from shared.src.governance.contract_governance_aggregate import (
        ISkillsGovernanceAggregate,
    )

    assert "execute" in ISkillsGovernanceAggregate.__abstractmethods__


def test_agent_implements_aggregate_contract():
    """CP-GOVERNANCE-003: the governance agent subclasses the aggregate contract."""
    from shared.src.governance.contract_governance_aggregate import (
        ISkillsGovernanceAggregate,
    )

    from governance.agent_governance_orchestrator import SkillsGovernanceAgent

    assert issubclass(SkillsGovernanceAgent, ISkillsGovernanceAggregate)
    assert not SkillsGovernanceAgent.__abstractmethods__, (
        "SkillsGovernanceAgent leaves the aggregate abstract"
    )


def test_capabilities_implement_their_protocols():
    """CP-GOVERNANCE-004: each governance capability subclasses its protocol."""
    from shared.src.design.contract_skills_protocol import (
        ISkillsLockerProtocol,
        ISkillsMoverProtocol,
        ISkillsPinerProtocol,
    )

    from governance.capabilities_skills_locker import SkillsLocker
    from governance.capabilities_skills_mover import SkillsMover
    from governance.capabilities_skills_piner import SkillsPiner

    assert issubclass(SkillsLocker, ISkillsLockerProtocol)
    assert issubclass(SkillsMover, ISkillsMoverProtocol)
    assert issubclass(SkillsPiner, ISkillsPinerProtocol)
