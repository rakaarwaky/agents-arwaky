"""Smoke tests for modules/shared — fast boot and import checks."""
from __future__ import annotations

import time


def test_import_shared_module():
    """SM-SHARED-001: modules.shared can be imported."""
    import modules.shared
    assert modules.shared is not None


def test_import_utility_modules():
    """SM-SHARED-002: utility modules can be imported."""
    from modules.shared.src import (
        utility_config_engine,
        utility_doc_pack,
        utility_envfile_parser,
        utility_jsonc_parser,
        utility_manifest_reader,
        utility_paths_resolver,
        utility_skill_registry,
        utility_toml_write,
        utility_tool_resolve,
    )

    assert utility_config_engine is not None
    assert utility_doc_pack is not None
    assert utility_envfile_parser is not None
    assert utility_jsonc_parser is not None
    assert utility_manifest_reader is not None
    assert utility_paths_resolver is not None
    assert utility_skill_registry is not None
    assert utility_toml_write is not None
    assert utility_tool_resolve is not None


def test_import_taxonomy_modules():
    """SM-SHARED-003: taxonomy modules can be imported."""
    from modules.shared.src import (
        taxonomy_common_constant,
        taxonomy_common_error,
        taxonomy_common_vo,
        taxonomy_skill_vo,
    )

    assert taxonomy_common_constant is not None
    assert taxonomy_common_error is not None
    assert taxonomy_common_vo is not None
    assert taxonomy_skill_vo is not None


def test_import_contracts():
    """SM-SHARED-004: contract modules can be imported."""
    from modules.shared.src import (
        contract_backup_aggregate,
        contract_backup_protocol,
        contract_check_aggregate,
        contract_check_protocol,
        contract_config_aggregate,
        contract_config_protocol,
        contract_daemon_aggregate,
        contract_daemon_protocol,
        contract_doctor_aggregate,
        contract_doctor_protocol,
        contract_harness_aggregate,
        contract_harness_protocol,
        contract_mcp_aggregate,
        contract_mcp_protocol,
        contract_service_aggregate,
        contract_service_protocol,
        contract_skill_aggregate,
        contract_skill_protocol,
        contract_tools_aggregate,
        contract_tools_protocol,
    )

    # All imports succeeded without errors
    assert True


def test_manifest_loads_quickly():
    """SM-SHARED-005: Manifest loads within 5 seconds."""
    from modules.shared.src.utility_manifest_reader import load_tools

    start = time.time()
    tools = load_tools()
    elapsed = time.time() - start

    assert elapsed < 5.0, f"Manifest load took {elapsed:.2f}s, expected <5s"
    assert isinstance(tools, list)


def test_skill_registry_quick():
    """SM-SHARED-006: Skill registry operations complete within 5 seconds."""
    from modules.shared.src.utility_skill_registry import get_all_skills, get_registered_tool_ids

    start = time.time()
    skills = get_all_skills()
    elapsed_skills = time.time() - start

    start = time.time()
    tools = get_registered_tool_ids()
    elapsed_tools = time.time() - start

    assert elapsed_skills < 5.0
    assert elapsed_tools < 5.0


def test_xdg_operations_quick():
    """SM-SHARED-007: XDG operations complete within 5 seconds."""
    from modules.shared.src.taxonomy_common_vo import (
        bin_home,
        cache_home,
        config_home,
        data_home,
        state_home,
    )

    start = time.time()
    _ = data_home()
    _ = config_home()
    _ = cache_home()
    _ = state_home()
    _ = bin_home()
    elapsed = time.time() - start

    assert elapsed < 5.0


def test_version_read_quick():
    """SM-SHARED-008: Version read completes within 5 seconds."""
    from modules.shared.src.taxonomy_common_vo import read_version

    start = time.time()
    version = read_version()
    elapsed = time.time() - start

    assert elapsed < 5.0
    assert isinstance(version, str)


def test_toml_write_quick():
    """SM-SHARED-009: TOML write operation completes within 5 seconds."""
    from modules.shared.src.utility_toml_write import write_toml

    start = time.time()
    result = write_toml({"key": "value", "nested": {"a": 1}})
    elapsed = time.time() - start

    assert elapsed < 5.0
    assert isinstance(result, str)


def test_jsonc_strip_quick():
    """SM-SHARED-010: JSONC strip operation completes within 5 seconds."""
    from modules.shared.src.utility_jsonc_parser import strip_jsonc_comments

    start = time.time()
    result = strip_jsonc_comments('{"key": "value"} // comment')
    elapsed = time.time() - start

    assert elapsed < 5.0
    assert isinstance(result, str)
