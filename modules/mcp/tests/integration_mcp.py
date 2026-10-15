"""Integration tests for modules/mcp — layers wired together."""

from __future__ import annotations

import tempfile
from pathlib import Path


def test_mcp_orchestrator_creation() -> None:
    """IT-MCP-001: the container wires the capabilities into the orchestrator."""
    from modules.mcp.src.capabilities_mcp_generator import (
        McpConfigLister,
        McpConfigWriter,
    )
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
    from modules.mcp.src.capabilities_mcp_generator import (
        McpConfigLister,
        McpConfigWriter,
    )

    lister = McpConfigLister()
    writer = McpConfigWriter()
    servers = generator.list_servers()
    assert servers is not None


def test_mcp_orchestrator_delegates() -> None:
    """IT-MCP-003: orchestrator routes list to lister and generate to writer."""
    from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator
    from modules.mcp.src.capabilities_mcp_generator import (
        McpConfigLister,
        McpConfigWriter,
    )
    from modules.shared.src.mcp.taxonomy_mcp_vo import McpOp, McpRequest

    lister = McpConfigLister()
    writer = McpConfigWriter()
    orch = McpOrchestrator(lister, writer)

    # list returns tuple (wrapped as McpResponse)
    response = orch.execute(McpRequest(McpOp("list")))
    assert isinstance(response, tuple)

    # generate returns ExitCode (int) wrapped as McpResponse
    response = orch.execute(McpRequest(McpOp("generate"), output=Path("test.json")))
    assert isinstance(response, int)


def test_mcp_generate_output() -> None:
    """IT-MCP-004: generate creates valid JSON output."""

    from pathlib import Path

    from modules.mcp.src.capabilities_mcp_generator import (
        McpConfigLister,
        McpConfigWriter,
    )

    lister = McpConfigLister()
    writer = McpConfigWriter()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        path = Path(f.name)
    try:
        generator.generate(path)
        content = path.read_text(encoding="utf-8")
        assert "mcpServers" in content
    finally:
        path.unlink(missing_ok=True)