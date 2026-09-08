"""Unit tests untuk tools/lib/xdg.py (P5-P1)."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools/lib"))

import xdg


def test_default_paths():
    assert str(xdg.bin_home()).endswith(".local/bin")
    assert str(xdg.data_home()).endswith(".local/share")


def test_env_override():
    old = os.environ.get("XDG_DATA_HOME")
    os.environ["XDG_DATA_HOME"] = "/tmp/xdg-test"
    try:
        assert str(xdg.data_home()) == "/tmp/xdg-test"
    finally:
        if old:
            os.environ["XDG_DATA_HOME"] = old
        else:
            os.environ.pop("XDG_DATA_HOME", None)


if __name__ == "__main__":
    test_default_paths()
    test_env_override()
    print("test_xdg.py: ALL PASSED")
