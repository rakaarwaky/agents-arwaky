"""Contract tests for modules/shared — prove protocol/interface implementations exist."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch


def test_manifest_reader_exports_load_tools():
    """CP-SHARED-001: load_tools function exists and is callable."""
    from modules.shared.src.utility_manifest_reader import load_tools

    assert callable(load_tools)
    result = load_tools()
    assert isinstance(result, list)


def test_manifest_reader_exports_find_tool():
    """CP-SHARED-002: find_tool function exists and is callable."""
    from modules.shared.src.utility_manifest_reader import find_tool

    assert callable(find_tool)
    result = find_tool("lint")
    assert result is None or hasattr(result, "id")


def test_envfile_parser_exports_functions():
    """CP-SHARED-003: envfile parser exports required functions."""
    from modules.shared.src.utility_envfile_parser import (
        load_first_env,
        parse_env_file,
        remove_env_keys,
        update_env_file,
    )

    assert callable(parse_env_file)
    assert callable(update_env_file)
    assert callable(remove_env_keys)
    assert callable(load_first_env)


def test_xdg_helpers_export_functions():
    """CP-SHARED-004: XDG path helpers are exported."""
    from modules.shared.src.taxonomy_common_vo import (
        agents_arwaky_config_dir,
        bin_home,
        cache_home,
        config_home,
        data_home,
        state_home,
        tool_cache_dir,
        tool_config_dir,
        tool_data_dir,
        tool_state_dir,
    )

    assert callable(data_home)
    assert callable(config_home)
    assert callable(cache_home)
    assert callable(state_home)
    assert callable(bin_home)
    assert callable(tool_data_dir)
    assert callable(tool_config_dir)
    assert callable(tool_cache_dir)
    assert callable(tool_state_dir)
    assert callable(agents_arwaky_config_dir)


def test_tool_resolve_exports_functions():
    """CP-SHARED-005: tool resolver exports required functions."""
    from modules.shared.src.utility_tool_resolve import is_submodule_missing, resolve_executable

    assert callable(resolve_executable)
    assert callable(is_submodule_missing)


def test_doc_pack_exports_functions():
    """CP-SHARED-006: doc pack exports required functions."""
    from modules.shared.src.utility_doc_pack import (
        audit_docs,
        check_backlog_rows,
        check_frd_template,
        check_fr_ids,
        check_spec_pairing,
        check_spec_status_leak,
        check_state_vocabulary,
        find_section,
        iter_doc_files,
        parse_tables,
        sections,
    )

    assert callable(audit_docs)
    assert callable(check_backlog_rows)
    assert callable(check_frd_template)
    assert callable(check_fr_ids)
    assert callable(check_spec_pairing)
    assert callable(check_spec_status_leak)
    assert callable(check_state_vocabulary)
    assert callable(find_section)
    assert callable(iter_doc_files)
    assert callable(parse_tables)
    assert callable(sections)


def test_config_engine_exports_functions():
    """CP-SHARED-007: config engine exports required functions."""
    from modules.shared.src.utility_config_engine import (
        detect_format,
        get_mcp_map,
        list_mcp_servers,
        load_file,
        merge_mcp_servers,
        remove_env_keys,
        remove_mcp_servers,
        save_file,
        set_env_keys,
    )

    assert callable(detect_format)
    assert callable(get_mcp_map)
    assert callable(list_mcp_servers)
    assert callable(load_file)
    assert callable(merge_mcp_servers)
    assert callable(remove_env_keys)
    assert callable(remove_mcp_servers)
    assert callable(save_file)
    assert callable(set_env_keys)


def test_jsonc_parser_exports_strip():
    """CP-SHARED-008: JSONC parser exports strip_jsonc_comments."""
    from modules.shared.src.utility_jsonc_parser import strip_jsonc_comments

    assert callable(strip_jsonc_comments)


def test_toml_write_exports_functions():
    """CP-SHARED-009: TOML writer exports required functions."""
    from modules.shared.src.utility_toml_write import (
        quote_key,
        toml_section,
        write_toml,
        write_toml_table,
        write_toml_value,
    )

    assert callable(write_toml)
    assert callable(write_toml_value)
    assert callable(quote_key)
    assert callable(toml_section)
    assert callable(write_toml_table)


def test_skill_vo_exports_functions():
    """CP-SHARED-010: skill value objects export required functions."""
    from modules.shared.src.taxonomy_skill_vo import (
        ensure_under,
        extract_skill_name,
        safe_child,
        safe_skill_name,
        sanitize_skill_name,
    )

    assert callable(extract_skill_name)
    assert callable(sanitize_skill_name)
    assert callable(safe_skill_name)
    assert callable(safe_child)
    assert callable(ensure_under)


def test_skill_registry_exports_functions():
    """CP-SHARED-011: skill registry exports required functions."""
    from modules.shared.src.utility_skill_registry import (
        extract_description,
        get_all_skills,
        get_registered_tool_ids,
        normalize_tool_id,
        provision_single_skill,
        prune_provisioned,
        remove_single_skill,
        resolve_single_skill_file,
        resolve_tool_skills,
        write_provenance,
    )

    assert callable(get_registered_tool_ids)
    assert callable(normalize_tool_id)
    assert callable(extract_description)
    assert callable(get_all_skills)
    assert callable(provision_single_skill)
    assert callable(prune_provisioned)
    assert callable(remove_single_skill)
    assert callable(resolve_single_skill_file)
    assert callable(resolve_tool_skills)
    assert callable(write_provenance)


def test_common_vo_exports_value_objects():
    """CP-SHARED-012: common value objects exist and can be instantiated."""
    from modules.shared.src.taxonomy_common_vo import (
        AuditFinding,
        DocFinding,
        InstallResult,
        PackFinding,
        Section,
        Table,
        Timestamp,
        Tool,
        ToolId,
        ToolSpec,
        UninstallResult,
        UpdateResult,
    )

    ts = Timestamp(123.456)
    assert ts.value == 123.456

    tid = ToolId("test-tool")
    assert tid.value == "test-tool"

    tool = Tool(
        id="test",
        category="dev",
        binary="test",
        is_mcp=False,
        description="test tool",
        path="/test",
    )
    assert tool.id == "test"

    finding = DocFinding(code="TEST-001", message="test message")
    assert finding.code == "TEST-001"
    assert finding.is_error is True


def test_common_error_hierarchy_exists():
    """CP-SHARED-013: domain error classes form expected hierarchy."""
    from modules.shared.src.taxonomy_common_error import (
        ArwakyError,
        DaemonStartError,
        DaemonStopError,
        GitUpdateError,
        ManifestParseError,
        SkillProvisionError,
        ConfigWriteError,
        ToolInstallError,
        ToolUpdateError,
        ToolUninstallError,
    )

    assert issubclass(ToolInstallError, ArwakyError)
    assert issubclass(ToolUpdateError, ArwakyError)
    assert issubclass(ToolUninstallError, ArwakyError)
    assert issubclass(DaemonStartError, ArwakyError)
    assert issubclass(DaemonStopError, ArwakyError)
    assert issubclass(SkillProvisionError, ArwakyError)
    assert issubclass(ConfigWriteError, ArwakyError)
    assert issubclass(GitUpdateError, ArwakyError)
    assert issubclass(ManifestParseError, ArwakyError)


def test_constants_are_defined():
    """CP-SHARED-014: key constants are defined in taxonomy_common_constant."""
    from modules.shared.src.taxonomy_common_constant import (
        BACKLOG_COLUMNS,
        DEFAULT_VERSION,
        DOC_NAMES,
        ERROR,
        REPO_ROOT,
        SPEC_DOCS,
        STATE_VOCAB,
        TOOL_RUNNERS,
    )

    assert isinstance(REPO_ROOT, Path)
    assert isinstance(DEFAULT_VERSION, str)
    assert isinstance(ERROR, str)
    assert isinstance(DOC_NAMES, tuple)
    assert isinstance(SPEC_DOCS, tuple)
    assert isinstance(BACKLOG_COLUMNS, tuple)
    assert isinstance(STATE_VOCAB, tuple)
    assert isinstance(TOOL_RUNNERS, dict)
