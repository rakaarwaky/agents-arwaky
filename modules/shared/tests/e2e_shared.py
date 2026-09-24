"""E2E tests for modules/shared — full request lifecycle tests."""
from __future__ import annotations


def test_manifest_e2e_workflow():
    """E2E-SHARED-001: Full manifest load and tool find workflow."""
    from modules.shared.src.utility_manifest_reader import load_tools, find_tool

    tools = load_tools()
    assert len(tools) >= 10

    lint_tool = find_tool("lint")
    assert lint_tool is not None
    assert lint_tool.id == "lint"


def test_envfile_e2e_workflow():
    """E2E-SHARED-002: Full envfile read/update/remove workflow."""
    import tempfile
    from pathlib import Path
    from modules.shared.src.utility_envfile_parser import parse_env_file, update_env_file, remove_env_keys

    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("")
        f.flush()
        path = Path(f.name)

    try:
        update_env_file(path, "KEY1", "value1")
        update_env_file(path, "KEY2", "value2")
        env = parse_env_file(path)
        assert env["KEY1"] == "value1"
        assert env["KEY2"] == "value2"

        remove_env_keys(path, ["KEY1"])
        env = parse_env_file(path)
        assert "KEY1" not in env
        assert env["KEY2"] == "value2"
    finally:
        path.unlink(missing_ok=True)


def test_xdg_paths_e2e_workflow():
    """E2E-SHARED-003: Full XDG path resolution workflow."""
    from modules.shared.src.taxonomy_common_vo import (
        data_home, config_home, cache_home, state_home, bin_home,
        tool_data_dir, tool_config_dir, tool_cache_dir
    )

    assert data_home().is_absolute()
    assert config_home().is_absolute()
    assert cache_home().is_absolute()
    assert state_home().is_absolute()
    assert bin_home().is_absolute()
    assert tool_data_dir("test").is_absolute()
    assert tool_config_dir("test").is_absolute()
    assert tool_cache_dir("test").is_absolute()
