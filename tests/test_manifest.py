"""Unit tests untuk tools/lib/manifest.py (P5-P1)."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools/lib"))

import manifest


def test_manifest_valid():
    tools = manifest.load_tools()
    assert len(tools) >= 10, "expected >=10 tools in manifest"
    assert all(t.id and t.binary and t.path for t in tools), "all tools need id/binary/path"


def test_find_tool():
    t = manifest.find_tool("lint")
    assert t is not None and t.id == "lint"


def test_find_tool_alias():
    # alias resmi di manifest (vision punya alias vision-arwaky)
    t = manifest.find_tool("vision-arwaky")
    assert t is not None and t.id == "vision"


if __name__ == "__main__":
    test_manifest_valid()
    test_find_tool()
    test_find_tool_alias()
    print("test_manifest.py: ALL PASSED")
