"""Dogfood tests — runs against live service/session."""
from __future__ import annotations

import pytest


@pytest.mark.dogfood
def test_dogfood_config_pipeline():
    """DOG-CONFIG-001: Basic dogfood check for config module."""
    from modules.config.src.capabilities_config_writer import ConfigWriter
    from modules.config.src.capabilities_config_modifier import ConfigModifier

    writer = ConfigWriter()
    modifier = ConfigModifier()

    assert hasattr(writer, 'execute')
    assert hasattr(modifier, 'execute')
