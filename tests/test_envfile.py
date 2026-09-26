"""Unit tests untuk modules/shared/src/utility_envfile_parser.py."""
import tempfile
from pathlib import Path

from modules.shared.src.utility_envfile_parser import (
    parse_env_file,
    remove_env_keys,
    update_env_file,
)


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
        assert env["A"] == "2", "update-in-place failed"


def test_remove_keys():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / ".env"
        update_env_file(f, "KEEP", "1")
        update_env_file(f, "DROP", "2")
        remove_env_keys(f, ["DROP"])
        env = parse_env_file(f)
        assert "DROP" not in env, "remove_env_keys failed"
        assert env.get("KEEP") == "1", "keep key lost"


if __name__ == "__main__":
    test_roundtrip_simple()
    test_roundtrip_quoted_value()
    test_update_existing()
    test_remove_keys()
    print("test_envfile.py: ALL PASSED")
