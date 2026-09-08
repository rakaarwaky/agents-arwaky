"""Unit tests untuk tools/lib/envfile.py (P5-P1)."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools/lib"))

from envfile import update_env_file, parse_env_file, remove_env_keys


def test_roundtrip_simple():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / ".env"
        update_env_file(f, "KEY", "simple-value")
        env = parse_env_file(f)
        assert env["KEY"] == "simple-value", "simple round-trip failed"


def test_roundtrip_quoted_value():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / ".env"
        update_env_file(f, "KEY", 'value with "quote" inside')
        env = parse_env_file(f)
        assert env["KEY"] == 'value with "quote" inside', "quoted round-trip failed"


def test_update_existing():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / ".env"
        update_env_file(f, "A", "1")
        update_env_file(f, "A", "2")
        env = parse_env_file(f)
        assert env["A"] == "2", "update should overwrite"


def test_remove_env_keys():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / ".env"
        update_env_file(f, "A", "1")
        update_env_file(f, "B", "2")
        removed = remove_env_keys(f, ["A"])
        assert "A" in removed
        env = parse_env_file(f)
        assert "A" not in env and env["B"] == "2"


if __name__ == "__main__":
    test_roundtrip_simple()
    test_roundtrip_quoted_value()
    test_update_existing()
    test_remove_env_keys()
    print("test_envfile.py: ALL PASSED")
