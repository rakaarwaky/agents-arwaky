"""Dogfood tests — runs against live service/session."""
from __future__ import annotations

import pytest


@pytest.mark.dogfood
def test_dogfood_daemon_pipeline():
    """DOG-DAEMON-001: Basic dogfood check for daemon module."""
    from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
    from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager

    anytype = AnytypeDaemonManager()
    ninerouter = NinerouterDaemonManager()

    assert not hasattr(anytype, 'execute')
    assert not hasattr(ninerouter, 'execute')
    for m in (anytype, ninerouter):
        for method in ("start", "stop", "restart", "status", "logs",
                      "install_unit", "remove_unit", "unit_status"):
            assert callable(getattr(m, method))
    assert repr(anytype) == "AnytypeDaemonManager()"
    assert repr(ninerouter) == "NinerouterDaemonManager()"
