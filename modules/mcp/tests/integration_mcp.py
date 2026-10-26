"""Integration tests for modules/mcp — layers wired together."""

from __future__ import annotations

import tempfile
from pathlib import Path


def test_mcp_orchestrator_creation() -> None:
    """IT-MCP-001: the container wires the capabilities into the orchestrator."""
    from modules.mcp.src.capabilities_mcp_generator import McpConfigLister
    from modules.mcp.src.capabilities_mcp_writer import McpConfigWriter
    from modules.mcp.src.root_mcp_container import create_mcp_feature

    feature = create_mcp_feature()
    assert feature is not None

    # Legacy facade path
    lister = McpConfigLister()
    writer = McpConfigWriter()
    from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator
    orch = McpOrchestrator(lister, writer)
    assert orch is not None


def test_mcp_generator_list_servers() -> None:
    """IT-MCP-002: list_servers returns server info from the manifest."""
    from modules.mcp.src.capabilities_mcp_generator import McpConfigLister

    lister = McpConfigLister()
    servers = lister.list_servers()
    assert servers is not None


def test_mcp_orchestrator_delegates(tmp_path) -> None:
    """IT-MCP-003: orchestrator routes list to lister and generate to writer."""
    from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator
    from modules.mcp.src.capabilities_mcp_generator import McpConfigLister
    from modules.mcp.src.capabilities_mcp_writer import McpConfigWriter
    from modules.shared.src.mcp.taxonomy_mcp_vo import McpOp, McpRequest

    lister = McpConfigLister()
    writer = McpConfigWriter()
    orch = McpOrchestrator(lister, writer)

    # list returns tuple (wrapped as McpResponse)
    response = orch.execute(McpRequest(McpOp("list")))
    assert isinstance(response, tuple)

    # generate returns ExitCode (int) wrapped as McpResponse
    response = orch.execute(McpRequest(McpOp("generate"), output=tmp_path / "test.json"))
    assert isinstance(response, int)


def test_generate_entry_count_matches_canonical_manifest(tmp_path) -> None:
    """MCP-01: generated entries exactly cover all MCP-enabled tools."""
    import json

    from modules.mcp.src.capabilities_mcp_writer import McpConfigWriter
    from modules.shared.src.common.utility_mcp_manifest import load_mcp_manifest

    writer = McpConfigWriter()
    output = tmp_path / "mcp.json"

    assert writer.generate(output) == 0
    generated = json.loads(output.read_text(encoding="utf-8"))["mcpServers"]
    manifest = load_mcp_manifest(writer._root)
    expected = {tool_id for tool_id, tool in manifest.items() if tool.get("mcp")}

    assert len(expected) == 8
    assert set(generated) == expected
    assert all(generated[tool_id]["command"] for tool_id in expected)


def test_generate_with_no_mcp_tools_writes_empty_valid_config(tmp_path) -> None:
    """FR-MCP-001: an empty manifest yields a valid empty config."""
    import json

    from modules.mcp.src.capabilities_mcp_writer import McpConfigWriter

    root = tmp_path / "repo"
    config = root / "config"
    config.mkdir(parents=True)
    (config / "manifest.json").write_text(
        json.dumps({"version": "1", "tools": []}), encoding="utf-8"
    )
    writer = McpConfigWriter()
    writer._root = root
    output = tmp_path / "empty.json"

    assert writer.generate(output) == 0
    assert json.loads(output.read_text(encoding="utf-8")) == {"mcpServers": {}}


def test_mcp_generate_output() -> None:
    """IT-MCP-004: generate creates valid JSON output."""

    from modules.mcp.src.capabilities_mcp_writer import McpConfigWriter

    writer = McpConfigWriter()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        path = Path(f.name)
    try:
        writer.generate(path)
        content = path.read_text(encoding="utf-8")
        assert "mcpServers" in content
    finally:
        path.unlink(missing_ok=True)