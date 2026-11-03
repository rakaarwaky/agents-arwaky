"""Dogfood tests — runs against live service/session."""
from __future__ import annotations

import pytest


@pytest.mark.dogfood
def test_dogfood_daemon_pipeline():
    """DOG-DAEMON-001: Basic dogfood check for daemon module."""
    from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager
    from modules.daemon.src.capabilities_omniroute_daemon import OmnirouteDaemonManager

    omniroute = OmnirouteDaemonManager()
    ninerouter = NinerouterDaemonManager()

    assert not hasattr(omniroute, 'execute')
    assert not hasattr(ninerouter, 'execute')
    for m in (omniroute, ninerouter):
        for method in ("start", "stop", "restart", "status", "logs",
                       "install_unit", "remove_unit", "unit_status"):
            assert callable(getattr(m, method))
    assert repr(omniroute) == "OmnirouteDaemonManager()"
    assert repr(ninerouter) == "NinerouterDaemonManager()"
