"""Smoke tests for modules/harness — fast import and basic checks."""
from __future__ import annotations

import time


def test_import_harness_modules():
    """SM-HARNESS-001: Harness modules can be imported."""
    from modules.harness.src import capabilities_harness_connector
    from modules.harness.src import capabilities_harness_disconnector
    from modules.harness.src import capabilities_harness_skills
    from modules.harness.src import agent_harness_orchestrator
    from modules.harness.src import root_harness_container

    assert capabilities_harness_connector is not None
    assert capabilities_harness_disconnector is not None
    assert capabilities_harness_skills is not None
    assert agent_harness_orchestrator is not None
    assert root_harness_container is not None


def test_harness_connector_init_quick():
    """SM-HARNESS-002: HarnessConnector initialization is quick."""
    from modules.harness.src.capabilities_harness_connector import HarnessConnector

    start = time.time()
    connector = HarnessConnector({})
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Initialization took {elapsed:.2f}s"


def test_harness_disconnector_init_quick():
    """SM-HARNESS-003: HarnessDisconnector initialization is quick."""
    from modules.harness.src.capabilities_harness_disconnector import HarnessDisconnector

    start = time.time()
    disconnector = HarnessDisconnector({})
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Initialization took {elapsed:.2f}s"


def test_harness_skills_init_quick():
    """SM-HARNESS-004: HarnessSkills initialization is quick."""
    from modules.harness.src.capabilities_harness_skills import HarnessSkills

    start = time.time()
    skills = HarnessSkills({})
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Initialization took {elapsed:.2f}s"


def test_container_creation_quick():
    """SM-HARNESS-005: Container creation is quick."""
    from modules.harness.src.root_harness_container import HarnessContainer

    start = time.time()
    container = HarnessContainer()
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Container creation took {elapsed:.2f}s"
