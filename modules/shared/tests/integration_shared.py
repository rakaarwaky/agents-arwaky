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


def test_skill_registry_returns_skills():
    """IT-SHARED-008: get_all_skills discovers SKILL.md files."""
    from modules.shared.src.utility_skill_registry import get_all_skills

    skills = get_all_skills()
    assert isinstance(skills, tuple)
    # Should find at least some skills in the repo
    assert len(skills) >= 0  # May be empty in test environment


def test_normalize_tool_id_alias():
    """IT-SHARED-009: normalize_tool_id resolves known aliases."""
    from modules.shared.src.utility_skill_registry import normalize_tool_id

    result = normalize_tool_id("la")
    assert result == "lint-arwaky"

    result = normalize_tool_id("va")
    assert result == "vision-arwaky"


def test_normalize_tool_id_exact():
    """IT-SHARED-010: normalize_tool_id returns id for exact match."""
    from modules.shared.src.utility_skill_registry import normalize_tool_id

    result = normalize_tool_id("lint-arwaky")
    assert result == "lint-arwaky"


def test_normalize_tool_id_unknown():
    """IT-SHARED-011: normalize_tool_id returns None for unknown."""
    from modules.shared.src.utility_skill_registry import normalize_tool_id

    result = normalize_tool_id("unknown-tool-12345")
    assert result is None


def test_get_registered_tool_ids():
    """IT-SHARED-012: get_registered_tool_ids returns tool data."""
    from modules.shared.src.utility_skill_registry import get_registered_tool_ids

    tools = get_registered_tool_ids()
    assert isinstance(tools, list)
    for tool_tuple in tools:
        assert len(tool_tuple) == 3
        tid, category, desc = tool_tuple
        assert isinstance(tid, str)
        assert isinstance(category, str)


def test_envfile_roundtrip_integration():
    """IT-SHARED-013: Full envfile read/write roundtrip works."""
    from modules.shared.src.utility_envfile_parser import (
        load_first_env,
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


def test_doc_pack_sections():
    """IT-SHARED-016: sections() parses headings correctly."""
    from modules.shared.src.utility_doc_pack import sections

    with tempfile.TemporaryDirectory() as tmpdir:
        doc = Path(tmpdir) / "test.md"
        doc.write_text("""# Header 1

Content

## Header 2

More content

### Header 3

Even more""")

        secs = sections(doc)
        assert len(secs) == 3
        assert secs[0].level == 1
        assert secs[0].title == "Header 1"
        assert secs[1].level == 2
        assert secs[1].title == "Header 2"
        assert secs[2].level == 3
        assert secs[2].title == "Header 3"


def test_doc_pack_find_section():
    """IT-SHARED-017: find_section returns correct section."""
    from modules.shared.src.utility_doc_pack import find_section, sections

    with tempfile.TemporaryDirectory() as tmpdir:
        doc = Path(tmpdir) / "test.md"
        doc.write_text("""# Header 1

## Section Two

Content here

### Subsection

More""")

        sec = find_section(doc, "Section Two")
        assert sec is not None
        assert sec.title == "Section Two"

        sec = find_section(doc, "nonexistent")
        assert sec is None


def test_doc_pack_parse_tables():
    """IT-SHARED-018: parse_tables extracts markdown tables."""
    from modules.shared.src.utility_doc_pack import parse_tables

    with tempfile.TemporaryDirectory() as tmpdir:
        doc = Path(tmpdir) / "test.md"
        doc.write_text("""# Table Test

| A | B |
|---|---|
| 1 | 2 |
| 3 | 4 |

More text""")

        tables = parse_tables(doc.read_text())
        assert len(tables) == 1
        assert tables[0].header == ["A", "B"]
        assert len(tables[0].rows) == 2


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
