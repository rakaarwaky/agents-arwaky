"""Unit tests for modules/daemon — test implementation details with mocking."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch


class TestAnytypeDaemonManagerInit:
    """Tests for AnytypeDaemonManager initialization."""

    def test_init_default_params(self):
        """UT-DAEMON-001: AnytypeDaemonManager initializes with default params."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        assert repr(manager) == "AnytypeDaemonManager()"

    def test_init_with_params(self):
        """UT-DAEMON-002: AnytypeDaemonManager accepts root and daemons."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager(root=Path("/test"), daemons=None)
        assert manager is not None


class TestAnytypeRichProtocol:
    """Tests for AnytypeDaemonManager exposing rich named protocol methods."""

    def test_start_method_exists(self):
        """UT-DAEMON-003: start() method exists and is callable."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'start', return_value=0) as mock_start:
            result = manager.start()
            assert result == 0

    def test_stop_method_exists(self):
        """UT-DAEMON-004: stop() method exists and is callable."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'stop', return_value=0) as mock_stop:
            result = manager.stop()
            assert result == 0

    def test_restart_method_exists(self):
        """UT-DAEMON-005: restart() method exists and is callable."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'restart', return_value=0) as mock_restart:
            result = manager.restart()
            assert result == 0

    def test_status_method_exists(self):
        """UT-DAEMON-006: status() method exists and is callable."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.shared.src.taxonomy_daemon_vo import DaemonStatus

        manager = AnytypeDaemonManager()
        with patch.object(
            manager, 'status',
            return_value=DaemonStatus("stopped", "stopped", False, "", False),
        ):
            result = manager.status()
            assert isinstance(result, DaemonStatus)

    def test_logs_method_exists(self):
        """UT-DAEMON-007: logs() method exists and is callable."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'logs', return_value=0) as mock_logs:
            result = manager.logs()
            assert result == 0

    def test_install_unit_method_exists(self):
        """UT-DAEMON-008: install_unit() method exists and is callable."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.shared.src.taxonomy_daemon_vo import DaemonUnit

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'install_unit', return_value=0) as mock_install:
            result = manager.install_unit(DaemonUnit("anytype-daemon.service"))
            assert result == 0

    def test_remove_unit_method_exists(self):
        """UT-DAEMON-009: remove_unit() method exists and is callable."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.shared.src.taxonomy_daemon_vo import DaemonUnit

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'remove_unit', return_value=0) as mock_remove:
            result = manager.remove_unit(DaemonUnit("anytype-daemon.service"))
            assert result == 0

    def test_unit_status_method_exists(self):
        """UT-DAEMON-010: unit_status() method exists and is callable."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.shared.src.taxonomy_daemon_vo import DaemonUnit

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'unit_status', return_value=0) as mock_us:
            result = manager.unit_status(DaemonUnit("anytype-daemon.service"))
            assert result == 0


class TestNinerouterRichProtocol:
    """Tests for NinerouterDaemonManager exposing rich named protocol methods."""

    def test_start_method_exists(self):
        """UT-DAEMON-011: start() method exists and is callable."""
        from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager

        manager = NinerouterDaemonManager()
        with patch.object(manager, 'start', return_value=0):
            result = manager.start()
            assert result == 0

    def test_status_method_exists(self):
        """UT-DAEMON-012: status() method exists and is callable."""
        from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager
        from modules.shared.src.taxonomy_daemon_vo import DaemonStatus

        manager = NinerouterDaemonManager()
        with patch.object(
            manager, 'status',
            return_value=DaemonStatus("stopped", "stopped", False, "", False),
        ):
            result = manager.status()
            assert isinstance(result, DaemonStatus)

    def test_install_unit_method_exists(self):
        """UT-DAEMON-013: install_unit() method exists and is callable."""
        from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager
        from modules.shared.src.taxonomy_daemon_vo import DaemonUnit

        manager = NinerouterDaemonManager()
        with patch.object(manager, 'install_unit', return_value=0):
            result = manager.install_unit(DaemonUnit("9router.service"))
            assert result == 0


class TestDaemonAggregateNoExecuteMethod:
    """The aggregate should NOT have a named execute method in the old style."""

    def test_orchestrator_has_single_execute(self):
        """UT-DAEMON-014: DaemonOrchestrator has a single execute() method."""
        from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
        from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        orch = DaemonOrchestrator(NinerouterDaemonManager(), AnytypeDaemonManager())
        assert callable(getattr(orch, "execute"))
        # All old aggregate methods are gone; only execute remains.
        for gone in ("start", "stop", "restart", "status", "logs",
                     "install_unit", "remove_unit", "unit_status", "list_known"):
            assert not hasattr(orch, gone) or gone == "execute"


class TestDaemonCapabilities:
    """Tests for daemon capability helper methods."""

    def test_api_ready_returns_bool(self):
        """UT-DAEMON-015: api_ready helper returns a bool."""
        from modules.daemon.src.capabilities_anytype_daemon import api_ready

        assert api_ready(timeout=0) in (True, False)

    def test_container_running_checks_podman(self):
        """UT-DAEMON-016: container_running helper returns a bool."""
        from modules.daemon.src.capabilities_anytype_daemon import container_running

        assert container_running() in (True, False)

    def test_container_exists_checks_podman(self):
        """UT-DAEMON-017: container_exists helper returns a bool."""
        from modules.daemon.src.capabilities_anytype_daemon import container_exists

        assert container_exists() in (True, False)

    def test_extract_api_key_finds_token(self):
        """UT-DAEMON-018: extract_api_key finds a token in multi-line output."""
        from modules.daemon.src.capabilities_anytype_daemon import _extract_api_key

        result = _extract_api_key("line1\n" + "a" * 25 + "\nline3")
        assert "a" * 25 in result

    def test_extract_api_key_fallback_to_last_line(self):
        """UT-DAEMON-019: extract_api_key falls back to the last line."""
        from modules.daemon.src.capabilities_anytype_daemon import _extract_api_key

        result = _extract_api_key("line1\nline2")
        assert result == "line2"

    def test_extract_api_key_empty_output(self):
        """UT-DAEMON-020: extract_api_key on empty output."""
        from modules.daemon.src.capabilities_anytype_daemon import _extract_api_key

        result = _extract_api_key("")
        assert result == ""

    def test_has_podman_returns_bool(self):
        """UT-DAEMON-021: has_podman helper returns a bool."""
        from modules.daemon.src.capabilities_anytype_daemon import has_podman

        assert has_podman() in (True, False)

    def test_image_exists_checks_podman(self):
        """UT-DAEMON-022: image_exists helper returns a bool."""
        from modules.daemon.src.capabilities_anytype_daemon import image_exists

        assert image_exists() in (True, False)


class TestDaemonOrchestrator:
    """Tests for DaemonOrchestrator."""

    def test_init_stores_managers(self):
        """UT-DAEMON-023: DaemonOrchestrator stores injected managers."""
        from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
        from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        orch = DaemonOrchestrator(NinerouterDaemonManager(), AnytypeDaemonManager())
        assert orch._ninerouter is not None
        assert orch._anytype is not None

    def test_execute_routes_to_correct_manager(self):
        """UT-DAEMON-024: DaemonOrchestrator.execute routes by op + name."""
        from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
        from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.shared.src.taxonomy_daemon_vo import (
            DaemonName,
            DaemonOp,
            DaemonRequest,
        )

        orch = DaemonOrchestrator(NinerouterDaemonManager(), AnytypeDaemonManager())
        # Patch the anytype manager's start to confirm routing.
        with patch.object(orch._anytype, "start", return_value=0) as mock_start:
            orch.execute(DaemonRequest(DaemonOp("start"), name=DaemonName("anytype")))
            mock_start.assert_called_once()
