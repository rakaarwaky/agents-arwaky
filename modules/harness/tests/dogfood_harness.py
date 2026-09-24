"""Dogfood tests — runs against live service/session."""
from __future__ import annotations

import pytest


@pytest.mark.dogfood
def test_dogfood_harness_pipeline():
    """DOG-HARNESS-001: Basic dogfood check for harness module."""
    from modules.harness.src.capabilities_harness_connector import HarnessConnector
    from modules.harness.src.capabilities_harness_disconnector import HarnessDisconnector
    from modules.harness.src.capabilities_harness_skills import HarnessSkills

    connector = HarnessConnector({})
    disconnector = HarnessDisconnector({})
    skills = HarnessSkills({})

    assert hasattr(connector, 'execute')
    assert hasattr(disconnector, 'execute')
    assert hasattr(skills, 'execute')
