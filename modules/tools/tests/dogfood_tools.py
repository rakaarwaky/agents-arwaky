"""Dogfood tests — runs against live service/session."""
from __future__ import annotations

import pytest


@pytest.mark.dogfood
def test_dogfood_tools_pipeline():
    """DOG-TOOLS-001: Basic dogfood check for tools module."""
    from modules.tools.src.capabilities_tools_installer import InstallerCapability
    from modules.tools.src.capabilities_tools_updater import UpdaterCapability
    from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability

    installer = InstallerCapability()
    updater = UpdaterCapability()
    uninstaller = UninstallerCapability()

    assert hasattr(installer, 'execute')
    assert hasattr(updater, 'execute')
    assert hasattr(uninstaller, 'execute')
