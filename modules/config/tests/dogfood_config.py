"""Dogfood tests — runs against live service/session."""
from __future__ import annotations

import pytest


@pytest.mark.dogfood
def test_dogfood_config_pipeline():
    """DOG-CONFIG-001: Basic dogfood check for config module."""
    from modules.config.src.capabilities_config_writer import ConfigWriter
    from modules.config.src.capabilities_config_modifier import ConfigModifier

    from modules.shared.src.contract_config_protocol import (
        IConfigReaderProtocol,
        IConfigModifierProtocol,
    )

    writer = ConfigWriter()
    modifier = ConfigModifier()

    # Each capability exposes its own named-method seam; neither carries a
    # dispatch bag, and neither implements the other's seam.
    for cap in (writer, modifier):
        assert not hasattr(cap, 'execute')

    assert isinstance(writer, IConfigReaderProtocol)
    for name in IConfigReaderProtocol.__abstractmethods__:
        assert callable(getattr(writer, name))

    assert isinstance(modifier, IConfigModifierProtocol)
    for name in IConfigModifierProtocol.__abstractmethods__:
        assert callable(getattr(modifier, name))
