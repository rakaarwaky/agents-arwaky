"""Dogfood tests — runs against live service/session."""
from __future__ import annotations

import pytest


@pytest.mark.dogfood
def test_dogfood_tools_pipeline():
    """DOG-TOOLS-001: Basic dogfood check for tools module."""
    from modules.shared.src.contract_tools_protocol import (
        IToolsInstallerProtocol,
        IToolsUninstallerProtocol,
        IToolsUpdaterProtocol,
    )
    from modules.tools.src.capabilities_tools_installer import InstallerCapability
    from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability
    from modules.tools.src.capabilities_tools_updater import UpdaterCapability

    # Each capability implements its rich protocol class outright and carries
    # no execute(op) dispatch bag.
    installer = InstallerCapability()
    updater = UpdaterCapability()
    uninstaller = UninstallerCapability()

    assert isinstance(installer, IToolsInstallerProtocol)
    assert isinstance(updater, IToolsUpdaterProtocol)
    assert isinstance(uninstaller, IToolsUninstallerProtocol)
    for cap in (installer, updater, uninstaller):
        assert not hasattr(cap, 'execute')

    assert callable(installer.install)
    assert callable(updater.update)
    assert callable(uninstaller.uninstall)
