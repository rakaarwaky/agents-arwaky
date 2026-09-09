"""Smoke tests for lib/ modules — verify imports, basic logic, no crashes."""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure lib/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))


# ---------------------------------------------------------------------------
# envfile
# ---------------------------------------------------------------------------
class TestEnvfile:
    def test_parse_env_file(self, tmp_path):
        from envfile import parse_env_file
        env_file = tmp_path / "test.env"
        env_file.write_text('FOO="bar"\nBAZ=123\n# comment\nEMPTY=\n')
        env = parse_env_file(env_file)
        assert env["FOO"] == "bar"
        assert env["BAZ"] == "123"
        assert "EMPTY" not in env  # empty values are skipped

    def test_update_env_file(self, tmp_path):
        from envfile import update_env_file
        env_file = tmp_path / "test.env"
        env_file.write_text('OLD="val"\n')
        update_env_file(env_file, "NEW", "hello")
        text = env_file.read_text()
        assert 'NEW="hello"' in text
        assert 'OLD="val"' in text

    def test_update_env_file_escapes_quotes(self, tmp_path):
        from envfile import update_env_file
        env_file = tmp_path / "test.env"
        update_env_file(env_file, "KEY", 'value"with"quotes')
        text = env_file.read_text()
        assert r'value\"with\"quotes' in text

    def test_remove_env_keys(self, tmp_path):
        from envfile import remove_env_keys
        env_file = tmp_path / "test.env"
        env_file.write_text('A=1\nB=2\nC=3\n')
        removed = remove_env_keys(env_file, ["A", "C"])
        assert set(removed) == {"A", "C"}
        text = env_file.read_text()
        assert "A=" not in text
        assert "C=" not in text
        assert "B=2" in text

    def test_load_first_env(self, tmp_path):
        from envfile import load_first_env
        env1 = tmp_path / "a.env"
        env2 = tmp_path / "b.env"
        env1.write_text("X=1\n")
        env2.write_text("Y=2\n")
        result = load_first_env([env2, env1])
        assert result["X"] == "1"


# ---------------------------------------------------------------------------
# engine
# ---------------------------------------------------------------------------
class TestEngine:
    def test_detect_format(self, tmp_path):
        from engine import detect_format
        assert detect_format(tmp_path / "a.json") == "json"
        assert detect_format(tmp_path / "a.yaml") == "yaml"
        assert detect_format(tmp_path / "a.yml") == "yaml"
        assert detect_format(tmp_path / "a.jsonc") == "jsonc"

    def test_load_save_json(self, tmp_path):
        from engine import load_file, save_file
        f = tmp_path / "test.json"
        f.write_text('{"key": "value"}')
        data, fmt = load_file(f)
        assert data["key"] == "value"
        assert fmt == "json"
        data["key"] = "updated"
        assert save_file(f, data, fmt)
        data2, _ = load_file(f)
        assert data2["key"] == "updated"

    def test_get_mcp_map(self):
        from engine import get_mcp_map
        data = {"mcpServers": {"s1": {}}}
        mcp, key = get_mcp_map(data)
        assert mcp is not None
        assert key == "mcpServers"
        assert "s1" in mcp

    def test_remove_mcp_servers(self, tmp_path):
        from engine import remove_mcp_servers
        f = tmp_path / "config.json"
        f.write_text(json.dumps({"mcpServers": {"a": {}, "b": {}}}))
        removed = remove_mcp_servers(f, ["a"])
        assert removed == ["a"]
        data = json.loads(f.read_text())
        assert "a" not in data["mcpServers"]
        assert "b" in data["mcpServers"]

    def test_set_env_keys(self, tmp_path):
        from engine import set_env_keys
        f = tmp_path / "test.env"
        f.write_text('OLD="val"\n')
        set_env_keys(f, {"NEW": "hello", "OLD": "updated"})
        text = f.read_text()
        assert 'NEW="hello"' in text
        assert 'OLD="updated"' in text

    def test_set_env_keys_escapes_quotes(self, tmp_path):
        from engine import set_env_keys
        f = tmp_path / "test.env"
        set_env_keys(f, {"KEY": 'val"ue'})
        text = f.read_text()
        assert 'val\\"ue' in text


# ---------------------------------------------------------------------------
# paths
# ---------------------------------------------------------------------------
class TestPaths:
    def test_repo_root_exists(self):
        from paths import repo_root
        root = repo_root()
        assert root.exists()
        assert (root / "tools" / "config" / "manifest.json").exists()

    def test_repo_root_validates_manifest(self):
        from paths import repo_root
        root = repo_root()
        # Should not raise (manifest exists)
        assert root.is_dir()


# ---------------------------------------------------------------------------
# manifest
# ---------------------------------------------------------------------------
class TestManifest:
    def test_load_tools(self):
        from manifest import load_tools
        tools = load_tools()
        assert len(tools) > 0
        ids = [t.id for t in tools]
        assert "skill" in ids

    def test_find_tool(self):
        from manifest import find_tool
        tool = find_tool("skill")
        assert tool is not None
        assert tool.id == "skill"
        assert find_tool("nonexistent") is None

    def test_tool_fields(self):
        from manifest import load_tools
        tools = load_tools()
        for t in tools:
            assert t.id, f"Tool missing id: {t}"
            assert t.binary, f"Tool {t.id} missing binary"
            assert t.path, f"Tool {t.id} missing path"


# ---------------------------------------------------------------------------
# skill_names
# ---------------------------------------------------------------------------
class TestSkillNames:
    def test_extract_skill_name(self, tmp_path):
        from skill_names import extract_skill_name
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("---\nname: my-skill\n---\n# Hello\n")
        assert extract_skill_name(skill_md) == "my-skill"

    def test_extract_skill_name_fallback(self, tmp_path):
        from skill_names import extract_skill_name
        skill_md = tmp_path / "fallback-name" / "SKILL.md"
        skill_md.parent.mkdir(parents=True)
        skill_md.write_text("no frontmatter here")
        assert extract_skill_name(skill_md) == "fallback-name"

    def test_sanitize_skill_name(self):
        from skill_names import sanitize_skill_name
        assert sanitize_skill_name("my skill!", "fallback") == "my-skill"
        # posixpath.basename strips directory traversal, leaving just "passwd"
        assert sanitize_skill_name("../../../etc/passwd", "fb") == "passwd"
        assert sanitize_skill_name("", "fallback") == "fallback"
        assert sanitize_skill_name("a" * 100, "fb") == "a" * 64

    def test_ensure_under(self, tmp_path):
        from skill_names import ensure_under
        base = tmp_path / "base"
        base.mkdir()
        child = base / "child"
        assert ensure_under(base, child) == child.resolve()
        outside = tmp_path / "other"
        outside.mkdir()
        with pytest.raises(ValueError, match="outside"):
            ensure_under(base, outside)


# ---------------------------------------------------------------------------
# xdg
# ---------------------------------------------------------------------------
class TestXdg:
    def test_data_home(self):
        from xdg import data_home
        p = data_home()
        assert p.is_absolute()

    def test_config_home(self):
        from xdg import config_home
        p = config_home()
        assert p.is_absolute()

    def test_tool_data_dir(self):
        from xdg import tool_data_dir
        p = tool_data_dir("test-tool-xyz")
        assert "test-tool-xyz" in str(p)

    def test_bin_home(self):
        from xdg import bin_home
        p = bin_home()
        assert p.is_absolute()
