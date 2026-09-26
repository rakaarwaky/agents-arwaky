"""Unit tests untuk XDG helpers di modules/shared/src/taxonomy_common_vo.py."""
import os

from modules.shared.src.taxonomy_common_vo import bin_home, data_home


def test_default_paths():
    old_data = os.environ.pop("XDG_DATA_HOME", None)
    old_bin = os.environ.pop("XDG_BIN_HOME", None)
    try:
        assert str(bin_home()).endswith(".local/bin")
        assert str(data_home()).endswith(".local/share")
    finally:
        if old_data is not None:
            os.environ["XDG_DATA_HOME"] = old_data
        if old_bin is not None:
            os.environ["XDG_BIN_HOME"] = old_bin


def test_env_override():
    old = os.environ.get("XDG_DATA_HOME")
    os.environ["XDG_DATA_HOME"] = "/tmp/xdg-test"
    try:
        assert str(data_home()) == "/tmp/xdg-test"
    finally:
        if old:
            os.environ["XDG_DATA_HOME"] = old
        else:
            os.environ.pop("XDG_DATA_HOME", None)


if __name__ == "__main__":
    test_default_paths()
    test_env_override()
    print("test_xdg.py: ALL PASSED")
