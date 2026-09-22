"""Unit tests untuk modules/shared/src/utility_manifest_reader.py."""
from modules.shared.src.utility_manifest_reader import find_tool, load_tools


def test_manifest_valid():
    tools = load_tools()
    assert len(tools) >= 10, "expected >=10 tools in manifest"
    assert all(t.id and t.binary and t.path for t in tools), "all tools need id/binary/path"


def test_find_tool():
    t = find_tool("lint")
    assert t is not None and t.id == "lint"


def test_find_tool_alias():
    # alias resmi di manifest (vision punya alias vision-arwaky)
    t = find_tool("vision-arwaky")
    assert t is not None and t.id == "vision"


if __name__ == "__main__":
    test_manifest_valid()
    test_find_tool()
    test_find_tool_alias()
    print("test_manifest.py: ALL PASSED")
