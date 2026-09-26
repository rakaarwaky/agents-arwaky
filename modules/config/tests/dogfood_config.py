"""Dogfood tests — runs against live service/session."""
from __future__ import annotations

import pytest


@pytest.mark.dogfood
def test_dogfood_config_pipeline():
    """DOG-CONFIG-001: Basic dogfood check for config module."""
    from modules.config.src.capabilities_config_writer import ConfigWriter
    from modules.config.src.capabilities_config_modifier import ConfigModifier

    from modules.shared.src.contract_config_protocol import IConfigProtocol

    writer = ConfigWriter()
    modifier = ConfigModifier()

    # Capabilities expose the rich protocol; neither carries a dispatch bag.
    for cap in (writer, modifier):
        assert isinstance(cap, IConfigProtocol)
        assert not hasattr(cap, 'execute')
        for name in IConfigProtocol.__abstractmethods__:
            assert callable(getattr(cap, name))
