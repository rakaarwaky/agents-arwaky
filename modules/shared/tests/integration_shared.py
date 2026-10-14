"""Integration tests for modules/shared — real wiring and manifest interactions."""
from __future__ import annotations

import tempfile
from pathlib import Path


def test_manifest_loads_real_tools():
    """IT-SHARED-001: load_tools returns actual tools from manifest."""
    from modules.shared.src.utility_manifest_reader import load_tools

    tools = load_tools()
    assert len(tools) >= 10, f"Expected at least 10 tools, got {len(tools)}"
    for tool in tools:
        assert tool.id, "Tool has no id"
        assert tool.binary, "Tool has no binary"
        assert tool.path, "Tool has no path"


def test_find_tool_by_id():
    """IT-SHARED-002: find_tool finds by exact id match."""
    from modules.shared.src.utility_manifest_reader import find_tool

    tool = find_tool("lint-arwaky")
    assert tool is not None
    assert tool.id == "lint-arwaky"


def test_find_tool_by_binary():
    """IT-SHARED-003: find_tool finds by binary name."""
    from modules.shared.src.utility_manifest_reader import find_tool

    tool = find_tool("lint-arwaky")
    assert tool is not None
    assert tool.id == "lint-arwaky"


def test_find_tool_by_alias():
    """IT-SHARED-004: find_tool finds by alias."""
    from modules.shared.src.utility_manifest_reader import find_tool

    tool = find_tool("la")
    assert tool is not None
    assert tool.id == "lint-arwaky"


def test_find_tool_missing():
    """IT-SHARED-005: find_tool returns None for missing tool."""
    from modules.shared.src.utility_manifest_reader import find_tool

    tool = find_tool("nonexistent-tool-12345")
    assert tool is None


def test_find_tool_empty():
    """IT-SHARED-006: find_tool returns None for empty query."""
    from modules.shared.src.utility_manifest_reader import find_tool

    tool = find_tool("")
    assert tool is None


def test_find_tool_whitespace():
    """IT-SHARED-007: find_tool strips whitespace."""
    from modules.shared.src.utility_manifest_reader import find_tool

    tool = find_tool("  lint  ")
    assert tool is not None
    # Legacy id still resolves to the canonical one.
    assert tool.id == "lint-arwaky"


def test_envfile_roundtrip_integration():
    """IT-SHARED-013: Full envfile read/write roundtrip works."""
    from modules.shared.src.utility_envfile_parser import (
        parse_env_file,
        remove_env_keys,
        update_env_file,
    )

    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("# Initial env\n")
        f.write("KEY1=value1\n")
        f.flush()
        path = Path(f.name)

    try:
        # Test parse
        env = parse_env_file(path)
        assert env["KEY1"] == "value1"

        # Test update
        update_env_file(path, "KEY2", "value2")
        env = parse_env_file(path)
        assert env["KEY1"] == "value1"
        assert env["KEY2"] == "value2"

        # Test remove
        removed = remove_env_keys(path, ["KEY1"])
        assert "KEY1" in removed
        env = parse_env_file(path)
        assert "KEY1" not in env
        assert env["KEY2"] == "value2"
    finally:
        path.unlink(missing_ok=True)


def test_config_engine_detect_format():
    """IT-SHARED-014: detect_format identifies correct format."""
    from modules.shared.src.utility_config_engine import detect_format

    with tempfile.TemporaryDirectory() as tmpdir:
        # JSON
        json_file = Path(tmpdir) / "test.json"
        json_file.write_text("{}")
        assert detect_format(json_file) == "json"

        # YAML
        yaml_file = Path(tmpdir) / "test.yaml"
        yaml_file.write_text("key: value\n")
        assert detect_format(yaml_file) == "yaml"

        # TOML
        toml_file = Path(tmpdir) / "test.toml"
        toml_file.write_text('[tool]\nkey = "value"\n')
        assert detect_format(toml_file) == "toml"


def test_config_engine_load_save_json():
    """IT-SHARED-015: Config engine can load and save JSON."""
    from modules.shared.src.utility_config_engine import load_file, save_file

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"key": "value", "num": 42}\n')
        f.flush()
        path = Path(f.name)

    try:
        data, fmt = load_file(path)
        assert fmt == "json"
        assert data["key"] == "value"
        assert data["num"] == 42

        data["new"] = "value"
        save_file(path, data, fmt)
        data2, _ = load_file(path)
        assert data2["new"] == "value"
    finally:
        path.unlink(missing_ok=True)


def test_xdg_paths_integration():
    """IT-SHARED-019: XDG paths work in real environment."""
    from modules.shared.src.taxonomy_common_vo import (
        agents_arwaky_config_dir,
        bin_home,
        cache_home,
        config_home,
        data_home,
        state_home,
    )

    # These should return valid paths
    assert data_home().is_absolute()
    assert config_home().is_absolute()
    assert cache_home().is_absolute()
    assert state_home().is_absolute()
    assert bin_home().is_absolute()
    assert agents_arwaky_config_dir().is_absolute()


def test_is_submodule_missing():
    """IT-SHARED-020: is_submodule_missing detects missing submodules."""
    from modules.shared.src.utility_tool_resolve import is_submodule_missing

    # This should not raise and return a boolean
    result = is_submodule_missing("internal/lint-arwaky")
    assert isinstance(result, bool)
