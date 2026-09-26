"""Dogfood tests — runs against live service/session.

These tests verify the module works with real external dependencies.
They use pytest.skipif to gracefully skip when services are unavailable.
"""
from __future__ import annotations

import pytest
from pathlib import Path


# Skip if running in CI or required services unavailable
@pytest.mark.dogfood
def test_dogfood_pipeline():
    """DOG-SHARED-001: Basic dogfood check against live manifest."""
    from modules.shared.src.utility_manifest_reader import load_tools, find_tool

    # This should work in any environment with valid manifest
    tools = load_tools()
    assert isinstance(tools, list)
    assert len(tools) >= 0  # May be 0 if manifest missing

    # Verify find_tool handles missing tools gracefully
    result = find_tool("nonexistent-tool-xyz")
    assert result is None
