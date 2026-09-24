"""Unit tests for modules/shared — utility functions and value objects."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch


class TestTimestamp:
    """Tests for Timestamp value object."""

    def test_timestamp_creation(self):
        """UT-SHARED-001: Timestamp can be created with float."""
        from modules.shared.src.taxonomy_common_vo import Timestamp

        ts = Timestamp(123.456)
        assert ts.value == 123.456

    def test_timestamp_str(self):
        """UT-SHARED-002: Timestamp __str__ returns string representation."""
        from modules.shared.src.taxonomy_common_vo import Timestamp

        ts = Timestamp(42.0)
        assert str(ts) == "42.0"

    def test_timestamp_repr(self):
        """UT-SHARED-003: Timestamp __repr__ is descriptive."""
        from modules.shared.src.taxonomy_common_vo import Timestamp

        ts = Timestamp(42.0)
        assert repr(ts) == "Timestamp(42.0)"

    def test_timestamp_equality(self):
        """UT-SHARED-004: Timestamp equality works correctly."""
        from modules.shared.src.taxonomy_common_vo import Timestamp

        ts1 = Timestamp(10.0)
        ts2 = Timestamp(10.0)
        ts3 = Timestamp(20.0)
        assert ts1 == ts2
        assert ts1 != ts3


class TestToolId:
    """Tests for ToolId value object."""

    def test_toolid_creation(self):
        """UT-SHARED-005: ToolId can be created with string."""
        from modules.shared.src.taxonomy_common_vo import ToolId

        tid = ToolId("lint")
        assert tid.value == "lint"

    def test_toolid_empty_raises(self):
        """UT-SHARED-006: ToolId rejects empty string."""
        from modules.shared.src.taxonomy_common_vo import ToolId

        try:
            ToolId("")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_toolid_str(self):
        """UT-SHARED-007: ToolId __str__ returns value."""
        from modules.shared.src.taxonomy_common_vo import ToolId

        tid = ToolId("test-tool")
        assert str(tid) == "test-tool"

    def test_toolid_equality(self):
        """UT-SHARED-008: ToolId equality works correctly."""
        from modules.shared.src.taxonomy_common_vo import ToolId

        tid1 = ToolId("test")
        tid2 = ToolId("test")
        tid3 = ToolId("other")
        assert tid1 == tid2
        assert tid1 != tid3

    def test_toolid_hash(self):
        """UT-SHARED-009: ToolId is hashable."""
        from modules.shared.src.taxonomy_common_vo import ToolId

        tid = ToolId("test")
        assert hash(tid) == hash("test")


class TestTool:
    """Tests for Tool value object."""

    def test_tool_creation(self):
        """UT-SHARED-010: Tool can be created with required fields."""
        from modules.shared.src.taxonomy_common_vo import Tool

        tool = Tool(
            id="test",
            category="dev",
            binary="test-cli",
            is_mcp=False,
            description="A test tool",
            path="/usr/bin/test",
        )
        assert tool.id == "test"
        assert tool.category == "dev"
        assert tool.binary == "test-cli"
        assert tool.is_mcp is False
        assert tool.description == "A test tool"
        assert tool.path == "/usr/bin/test"

    def test_tool_default_fields(self):
        """UT-SHARED-011: Tool has default values for optional fields."""
        from modules.shared.src.taxonomy_common_vo import Tool

        tool = Tool(
            id="test",
            category="dev",
            binary="test-cli",
            is_mcp=False,
            description="A test tool",
            path="/usr/bin/test",
        )
        assert tool.alias is None
        assert tool.mcp_binary is None

    def test_tool_is_frozen(self):
        """UT-SHARED-012: Tool is immutable (frozen dataclass)."""
        from modules.shared.src.taxonomy_common_vo import Tool

        tool = Tool(
            id="test",
            category="dev",
            binary="test-cli",
            is_mcp=False,
            description="A test tool",
            path="/usr/bin/test",
        )
        try:
            tool.id = "modified"
            assert False, "Should have raised FrozenInstanceError"
        except Exception:
            pass


class TestAuditFinding:
    """Tests for AuditFinding value object."""

    def test_audit_finding_creation(self):
        """UT-SHARED-013: AuditFinding can be created."""
        from modules.shared.src.taxonomy_common_vo import AuditFinding

        finding = AuditFinding(code="TEST-001", message="test message")
        assert finding.code == "TEST-001"
        assert finding.message == "test message"
        assert finding.path == ""
        assert finding.severity == "error"

    def test_audit_finding_is_error(self):
        """UT-SHARED-014: AuditFinding.is_error returns True for error severity."""
        from modules.shared.src.taxonomy_common_vo import AuditFinding

        finding = AuditFinding(code="TEST-001", message="test", severity="error")
        assert finding.is_error is True


class TestDocFinding:
    """Tests for DocFinding value object."""

    def test_doc_finding_creation(self):
        """UT-SHARED-015: DocFinding can be created."""
        from modules.shared.src.taxonomy_common_vo import DocFinding

        finding = DocFinding(code="TEST-001", message="test message")
        assert finding.code == "TEST-001"
        assert finding.message == "test message"
        assert finding.path == ""

    def test_doc_finding_default_severity(self):
        """UT-SHARED-016: DocFinding defaults to ERROR severity."""
        from modules.shared.src.taxonomy_common_vo import DocFinding, ERROR

        finding = DocFinding(code="TEST-001", message="test")
        assert finding.severity == ERROR
        assert finding.is_error is True

    def test_doc_finding_warning(self):
        """UT-SHARED-017: DocFinding can have warning severity."""
        from modules.shared.src.taxonomy_common_vo import DocFinding

        finding = DocFinding(code="TEST-001", message="test", severity="warning")
        assert finding.is_error is False


class TestSection:
    """Tests for Section value object."""

    def test_section_creation(self):
        """UT-SHARED-018: Section can be created."""
        from modules.shared.src.taxonomy_common_vo import Section

        section = Section(level=2, title="Test", body="content", line=1)
        assert section.level == 2
        assert section.title == "Test"
        assert section.body == "content"
        assert section.line == 1


class TestTable:
    """Tests for Table value object."""

    def test_table_creation(self):
        """UT-SHARED-019: Table can be created."""
        from modules.shared.src.taxonomy_common_vo import Table

        table = Table(
            header=["A", "B"],
            rows=[(1, ["1", "2"])],
            line=1,
        )
        assert table.header == ["A", "B"]
        assert table.rows == [(1, ["1", "2"])]
        assert table.line == 1


class TestPackFinding:
    """Tests for PackFinding value object."""

    def test_pack_finding_creation(self):
        """UT-SHARED-020: PackFinding can be created."""
        from modules.shared.src.taxonomy_common_vo import PackFinding

        finding = PackFinding(code="TEST-001", message="test message")
        assert finding.code == "TEST-001"
        assert finding.message == "test message"
        assert finding.path == ""


class TestParseEnvFile:
    """Tests for parse_env_file function."""

    def test_parse_simple(self):
        """UT-SHARED-021: parse_env_file handles simple KEY=VALUE."""
        from modules.shared.src.utility_envfile_parser import parse_env_file

        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("KEY=value\n")
            f.flush()
            result = parse_env_file(Path(f.name))
            assert result == {"KEY": "value"}
            os.unlink(f.name)

    def test_parse_skips_comments(self):
        """UT-SHARED-022: parse_env_file skips comment lines."""
        from modules.shared.src.utility_envfile_parser import parse_env_file

        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("# This is a comment\n")
            f.write("KEY=value\n")
            f.flush()
            result = parse_env_file(Path(f.name))
            assert result == {"KEY": "value"}
            os.unlink(f.name)

    def test_parse_empty_file(self):
        """UT-SHARED-023: parse_env_file handles empty file."""
        from modules.shared.src.utility_envfile_parser import parse_env_file

        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("")
            f.flush()
            result = parse_env_file(Path(f.name))
            assert result == {}
            os.unlink(f.name)

    def test_parse_nonexistent(self):
        """UT-SHARED-024: parse_env_file returns empty dict for missing file."""
        from modules.shared.src.utility_envfile_parser import parse_env_file

        result = parse_env_file(Path("/nonexistent/file.env"))
        assert result == {}

    def test_parse_quoted_values(self):
        """UT-SHARED-025: parse_env_file handles quoted values."""
        from modules.shared.src.utility_envfile_parser import parse_env_file

        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write('KEY="value with spaces"\n')
            f.write("KEY2='single quotes'\n")
            f.flush()
            result = parse_env_file(Path(f.name))
            assert result["KEY"] == "value with spaces"
            assert result["KEY2"] == "single quotes"
            os.unlink(f.name)

    def test_parse_multiline_value(self):
        """UT-SHARED-026: parse_env_file handles multiline values."""
        from modules.shared.src.utility_envfile_parser import parse_env_file

        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write('KEY=line1\n')
            f.write('KEY2=line2\n')
            f.flush()
            result = parse_env_file(Path(f.name))
            assert result["KEY"] == "line1"
            assert result["KEY2"] == "line2"
            os.unlink(f.name)


class TestUpdateEnvFile:
    """Tests for update_env_file function."""

    def test_update_adds_key(self):
        """UT-SHARED-027: update_env_file adds new key."""
        from modules.shared.src.utility_envfile_parser import parse_env_file, update_env_file

        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("")
            f.flush()
            update_env_file(Path(f.name), "KEY", "value")
            result = parse_env_file(Path(f.name))
            assert result["KEY"] == "value"
            os.unlink(f.name)

    def test_update_overwrites_existing(self):
        """UT-SHARED-028: update_env_file overwrites existing key."""
        from modules.shared.src.utility_envfile_parser import parse_env_file, update_env_file

        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("KEY=old\n")
            f.flush()
            update_env_file(Path(f.name), "KEY", "new")
            result = parse_env_file(Path(f.name))
            assert result["KEY"] == "new"
            os.unlink(f.name)

    def test_update_escaped_quotes(self):
        """UT-SHARED-029: update_env_file escapes quotes in values."""
        from modules.shared.src.utility_envfile_parser import parse_env_file, update_env_file

        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("")
            f.flush()
            update_env_file(Path(f.name), "KEY", 'value with "quotes"')
            result = parse_env_file(Path(f.name))
            assert result["KEY"] == 'value with "quotes"'
            os.unlink(f.name)


class TestRemoveEnvKeys:
    """Tests for remove_env_keys function."""

    def test_remove_single_key(self):
        """UT-SHARED-030: remove_env_keys removes single key."""
        from modules.shared.src.utility_envfile_parser import parse_env_file, remove_env_keys, update_env_file

        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("KEY1=value1\n")
            f.write("KEY2=value2\n")
            f.flush()
            remove_env_keys(Path(f.name), ["KEY1"])
            result = parse_env_file(Path(f.name))
            assert "KEY1" not in result
            assert result["KEY2"] == "value2"
            os.unlink(f.name)

    def test_remove_multiple_keys(self):
        """UT-SHARED-031: remove_env_keys removes multiple keys."""
        from modules.shared.src.utility_envfile_parser import parse_env_file, remove_env_keys, update_env_file

        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("KEY1=value1\n")
            f.write("KEY2=value2\n")
            f.write("KEY3=value3\n")
            f.flush()
            removed = remove_env_keys(Path(f.name), ["KEY1", "KEY3"])
            result = parse_env_file(Path(f.name))
            assert "KEY1" not in result
            assert "KEY3" not in result
            assert result["KEY2"] == "value2"
            assert sorted(removed) == ["KEY1", "KEY3"]
            os.unlink(f.name)

    def test_remove_nonexistent_key(self):
        """UT-SHARED-032: remove_env_keys handles nonexistent key."""
        from modules.shared.src.utility_envfile_parser import parse_env_file, remove_env_keys, update_env_file

        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            removed = remove_env_keys(Path(f.name), ["KEY2"])
            assert removed == []
            os.unlink(f.name)


class TestLoadFirstEnv:
    """Tests for load_first_env function."""

    def test_load_first_found(self):
        """UT-SHARED-033: load_first_env returns first existing env file."""
        from modules.shared.src.utility_envfile_parser import load_first_env

        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("KEY=value\n")
            f.flush()
            result = load_first_env([Path(f.name)])
            assert result["KEY"] == "value"
            os.unlink(f.name)

    def test_load_first_skips_missing(self):
        """UT-SHARED-034: load_first_env skips missing files."""
        from modules.shared.src.utility_envfile_parser import load_first_env

        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("KEY=value\n")
            f.flush()
            result = load_first_env([Path("/nonexistent"), Path(f.name)])
            assert result["KEY"] == "value"
            os.unlink(f.name)

    def test_load_first_empty(self):
        """UT-SHARED-035: load_first_env returns empty dict when no files exist."""
        from modules.shared.src.utility_envfile_parser import load_first_env

        result = load_first_env([Path("/nonexistent1"), Path("/nonexistent2")])
        assert result == {}


class TestDataHome:
    """Tests for XDG helper functions."""

    def test_data_home_default(self):
        """UT-SHARED-036: data_home returns default path."""
        from modules.shared.src.taxonomy_common_vo import data_home

        old = os.environ.pop("XDG_DATA_HOME", None)
        try:
            result = data_home()
            assert str(result).endswith(".local/share")
        finally:
            if old:
                os.environ["XDG_DATA_HOME"] = old

    def test_data_home_override(self):
        """UT-SHARED-037: data_home respects XDG_DATA_HOME."""
        from modules.shared.src.taxonomy_common_vo import data_home

        os.environ["XDG_DATA_HOME"] = "/custom/data"
        try:
            result = data_home()
            assert str(result) == "/custom/data"
        finally:
            os.environ.pop("XDG_DATA_HOME", None)

    def test_config_home_default(self):
        """UT-SHARED-038: config_home returns default path."""
        from modules.shared.src.taxonomy_common_vo import config_home

        old = os.environ.pop("XDG_CONFIG_HOME", None)
        try:
            result = config_home()
            assert str(result).endswith(".config")
        finally:
            if old:
                os.environ["XDG_CONFIG_HOME"] = old

    def test_cache_home_default(self):
        """UT-SHARED-039: cache_home returns default path."""
        from modules.shared.src.taxonomy_common_vo import cache_home

        old = os.environ.pop("XDG_CACHE_HOME", None)
        try:
            result = cache_home()
            assert str(result).endswith(".cache")
        finally:
            if old:
                os.environ["XDG_CACHE_HOME"] = old

    def test_state_home_default(self):
        """UT-SHARED-040: state_home returns default path."""
        from modules.shared.src.taxonomy_common_vo import state_home

        old = os.environ.pop("XDG_STATE_HOME", None)
        try:
            result = state_home()
            assert str(result).endswith(".local/state")
        finally:
            if old:
                os.environ["XDG_STATE_HOME"] = old

    def test_bin_home_default(self):
        """UT-SHARED-041: bin_home returns default path."""
        from modules.shared.src.taxonomy_common_vo import bin_home

        old = os.environ.pop("XDG_BIN_HOME", None)
        try:
            result = bin_home()
            assert str(result).endswith(".local/bin")
        finally:
            if old:
                os.environ["XDG_BIN_HOME"] = old


class TestToolDirs:
    """Tests for tool-specific XDG directory functions."""

    def test_tool_data_dir(self):
        """UT-SHARED-042: tool_data_dir returns correct path."""
        from modules.shared.src.taxonomy_common_vo import tool_data_dir

        result = tool_data_dir("test-tool")
        assert result.name == "test-tool"
        assert "share" in str(result)

    def test_tool_config_dir(self):
        """UT-SHARED-043: tool_config_dir returns correct path."""
        from modules.shared.src.taxonomy_common_vo import tool_config_dir

        result = tool_config_dir("test-tool")
        assert result.name == "test-tool"
        assert "config" in str(result)

    def test_tool_cache_dir(self):
        """UT-SHARED-044: tool_cache_dir returns correct path."""
        from modules.shared.src.taxonomy_common_vo import tool_cache_dir

        result = tool_cache_dir("test-tool")
        assert result.name == "test-tool"
        assert "cache" in str(result)

    def test_tool_state_dir(self):
        """UT-SHARED-045: tool_state_dir returns correct path."""
        from modules.shared.src.taxonomy_common_vo import tool_state_dir

        result = tool_state_dir("test-tool")
        assert result.name == "test-tool.state"
        assert "share" in str(result)

    def test_agents_arwaky_config_dir(self):
        """UT-SHARED-046: agents_arwaky_config_dir returns correct path."""
        from modules.shared.src.taxonomy_common_vo import agents_arwaky_config_dir

        result = agents_arwaky_config_dir()
        assert result.name == "agents-arwaky"
        assert "config" in str(result)


class TestBump:
    """Tests for version bumping."""

    def test_bump_major(self):
        """UT-SHARED-047: bump major version."""
        from modules.shared.src.taxonomy_common_vo import bump

        result = bump("1.2.3", "major")
        assert result == "2.0.0"

    def test_bump_minor(self):
        """UT-SHARED-048: bump minor version."""
        from modules.shared.src.taxonomy_common_vo import bump

        result = bump("1.2.3", "minor")
        assert result == "1.3.0"

    def test_bump_patch(self):
        """UT-SHARED-049: bump patch version."""
        from modules.shared.src.taxonomy_common_vo import bump

        result = bump("1.2.3", "patch")
        assert result == "1.2.4"

    def test_bump_invalid_version(self):
        """UT-SHARED-050: bump raises ValueError for invalid version."""
        from modules.shared.src.taxonomy_common_vo import bump

        try:
            bump("invalid", "patch")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_bump_unknown_part(self):
        """UT-SHARED-051: bump raises ValueError for unknown part."""
        from modules.shared.src.taxonomy_common_vo import bump

        try:
            bump("1.0.0", "unknown")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


class TestReadVersion:
    """Tests for read_version function."""

    def test_read_version_existing(self):
        """UT-SHARED-052: read_version returns version from file."""
        from modules.shared.src.taxonomy_common_vo import read_version
        from modules.shared.src import taxonomy_common_constant
        from pathlib import Path
        import tempfile

        # Create a temp dir with config/version.txt
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir()
            version_file = config_dir / "version.txt"
            version_file.write_text("1.2.3")

            # Temporarily replace REPO_ROOT in both modules
            original_root = taxonomy_common_constant.REPO_ROOT
            try:
                taxonomy_common_constant.REPO_ROOT = Path(tmpdir)
                # Also need to patch the module-level reference
                import modules.shared.src.taxonomy_common_vo as vo_module
                original_repo_root = vo_module.repo_root
                vo_module.repo_root = Path(tmpdir)
                try:
                    result = read_version()
                    assert result == "1.2.3"
                finally:
                    vo_module.repo_root = original_repo_root
            finally:
                taxonomy_common_constant.REPO_ROOT = original_root

    def test_read_version_missing(self):
        """UT-SHARED-053: read_version returns default when file missing."""
        from modules.shared.src.taxonomy_common_vo import read_version
        from modules.shared.src import taxonomy_common_constant

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(taxonomy_common_constant, 'REPO_ROOT', Path(tmpdir)):
                result = read_version()
                assert result == taxonomy_common_constant.DEFAULT_VERSION


class TestStripJsoncComments:
    """Tests for JSONC comment stripping."""

    def test_strip_simple_comment(self):
        """UT-SHARED-054: strip_jsonc_comments removes single-line comments."""
        from modules.shared.src.utility_jsonc_parser import strip_jsonc_comments

        result = strip_jsonc_comments('{"key": "value"} // comment')
        assert "//" not in result
        assert '"value"' in result

    def test_strip_multiline_comment(self):
        """UT-SHARED-055: strip_jsonc_comments removes multi-line comments."""
        from modules.shared.src.utility_jsonc_parser import strip_jsonc_comments

        result = strip_jsonc_comments('{"key": "value"} /* comment */')
        assert "/*" not in result
        assert "//" not in result
        assert '"value"' in result

    def test_strip_preserves_strings(self):
        """UT-SHARED-056: strip_jsonc_comments preserves slash in strings."""
        from modules.shared.src.utility_jsonc_parser import strip_jsonc_comments

        result = strip_jsonc_comments('{"url": "http://example.com"}')
        assert "http://example.com" in result

    def test_strip_empty_string(self):
        """UT-SHARED-057: strip_jsonc_comments handles empty string."""
        from modules.shared.src.utility_jsonc_parser import strip_jsonc_comments

        result = strip_jsonc_comments("")
        assert result == ""


class TestWriteTomlValue:
    """Tests for TOML value writing."""

    def test_write_bool_true(self):
        """UT-SHARED-058: write_toml_value handles boolean True."""
        from modules.shared.src.utility_toml_write import write_toml_value

        result = write_toml_value(True)
        assert result == "true"

    def test_write_bool_false(self):
        """UT-SHARED-059: write_toml_value handles boolean False."""
        from modules.shared.src.utility_toml_write import write_toml_value

        result = write_toml_value(False)
        assert result == "false"

    def test_write_int(self):
        """UT-SHARED-060: write_toml_value handles integer."""
        from modules.shared.src.utility_toml_write import write_toml_value

        result = write_toml_value(42)
        assert result == "42"

    def test_write_float(self):
        """UT-SHARED-061: write_toml_value handles float."""
        from modules.shared.src.utility_toml_write import write_toml_value

        result = write_toml_value(3.14)
        assert result == "3.14"

    def test_write_string(self):
        """UT-SHARED-062: write_toml_value handles string with escaping."""
        from modules.shared.src.utility_toml_write import write_toml_value

        result = write_toml_value('hello "world"')
        assert '"' in result
        assert "hello" in result

    def test_write_empty_list(self):
        """UT-SHARED-063: write_toml_value handles empty list."""
        from modules.shared.src.utility_toml_write import write_toml_value

        result = write_toml_value([])
        assert result == "[]"

    def test_write_list(self):
        """UT-SHARED-064: write_toml_value handles list."""
        from modules.shared.src.utility_toml_write import write_toml_value

        result = write_toml_value([1, 2, 3])
        assert "[1, 2, 3]" == result

    def test_write_empty_dict(self):
        """UT-SHARED-065: write_toml_value handles empty dict."""
        from modules.shared.src.utility_toml_write import write_toml_value

        result = write_toml_value({})
        assert result == "{}"


class TestQuoteKey:
    """Tests for TOML key quoting."""

    def test_quote_simple_key(self):
        """UT-SHARED-066: quote_key handles simple key."""
        from modules.shared.src.utility_toml_write import quote_key

        result = quote_key("key")
        assert result == "key"

    def test_quote_special_key(self):
        """UT-SHARED-067: quote_key handles special characters."""
        from modules.shared.src.utility_toml_write import quote_key

        result = quote_key("key-name")
        assert result == "key-name"

    def test_quote_with_spaces(self):
        """UT-SHARED-068: quote_key escapes keys with spaces."""
        from modules.shared.src.utility_toml_write import quote_key

        result = quote_key("key name")
        assert '"' in result


class TestExtractSkillName:
    """Tests for skill name extraction."""

    def test_extract_from_frontmatter(self):
        """UT-SHARED-069: extract_skill_name reads from frontmatter."""
        from modules.shared.src.taxonomy_skill_vo import extract_skill_name

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text("---\nname: my-skill\ndescription: test\n---\n\n# Skill\n")
            result = extract_skill_name(skill_file)
            assert result == "my-skill"

    def test_extract_fallback_to_dir(self):
        """UT-SHARED-070: extract_skill_name falls back to dir name."""
        from modules.shared.src.taxonomy_skill_vo import extract_skill_name

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "fallback-skill"
            skill_dir.mkdir()
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text("No frontmatter\n")
            result = extract_skill_name(skill_file)
            assert result == "fallback-skill"

    def test_extract_missing_file(self):
        """UT-SHARED-071: extract_skill_name handles missing file gracefully."""
        from modules.shared.src.taxonomy_skill_vo import extract_skill_name

        # Use a path where parent directory name can be used as fallback
        skill_file = Path("/tmp/nonexistent/SKILL.md")
        result = extract_skill_name(skill_file)
        # Fallback to parent directory name
        assert result == "nonexistent"


class TestSanitizeSkillName:
    """Tests for skill name sanitization."""

    def test_sanitize_basic(self):
        """UT-SHARED-072: sanitize_skill_name handles basic input."""
        from modules.shared.src.taxonomy_skill_vo import sanitize_skill_name

        result = sanitize_skill_name("my-skill", "fallback")
        assert result == "my-skill"

    def test_sanitize_replaces_special(self):
        """UT-SHARED-073: sanitize_skill_name replaces special chars."""
        from modules.shared.src.taxonomy_skill_vo import sanitize_skill_name

        result = sanitize_skill_name("my skill!", "fallback")
        assert "my-skill" in result

    def test_sanitize_truncates_long(self):
        """UT-SHARED-074: sanitize_skill_name truncates to 64 chars."""
        from modules.shared.src.taxonomy_skill_vo import sanitize_skill_name

        long_name = "a" * 100
        result = sanitize_skill_name(long_name, "fallback")
        assert len(result) <= 64

    def test_sanitize_empty_uses_fallback(self):
        """UT-SHARED-075: sanitize_skill_name uses fallback when empty."""
        from modules.shared.src.taxonomy_skill_vo import sanitize_skill_name

        result = sanitize_skill_name("", "my-fallback")
        assert "my-fallback" in result


class TestSafeChild:
    """Tests for safe_child function."""

    def test_safe_child_basic(self):
        """UT-SHARED-076: safe_child creates basic child path."""
        from modules.shared.src.taxonomy_skill_vo import safe_child

        base = Path("/tmp/base")
        result = safe_child(base, "skill")
        assert result == base / "skill"

    def test_safe_child_rejects_dotdot(self):
        """UT-SHARED-077: safe_child rejects '..' in name."""
        from modules.shared.src.taxonomy_skill_vo import safe_child

        base = Path("/tmp/base")
        try:
            safe_child(base, "../escape")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_safe_child_rejects_path_sep(self):
        """UT-SHARED-078: safe_child rejects path separators."""
        from modules.shared.src.taxonomy_skill_vo import safe_child

        base = Path("/tmp/base")
        try:
            safe_child(base, "skill/subdir")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


class TestResolveExecutable:
    """Tests for resolve_executable function."""

    def test_resolve_existing(self):
        """UT-SHARED-079: resolve_executable finds existing binary."""
        from modules.shared.src.utility_tool_resolve import resolve_executable

        result = resolve_executable("python3")
        assert result is not None

    def test_resolve_missing(self):
        """UT-SHARED-080: resolve_executable returns None for missing binary."""
        from modules.shared.src.utility_tool_resolve import resolve_executable

        result = resolve_executable("nonexistent-binary-12345")
        assert result is None
