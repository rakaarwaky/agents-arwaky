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


class TestAnytypeExecuteDispatch:
    """Tests for AnytypeDaemonManager.execute dispatching."""

    def test_execute_start_dispatches(self):
        """UT-DAEMON-003: execute('start') dispatches to start()."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'start', return_value=0) as mock_start:
            result = manager.execute("start")
            mock_start.assert_called_once()
            assert result == 0

    def test_execute_stop_dispatches(self):
        """UT-DAEMON-004: execute('stop') dispatches to stop()."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'stop', return_value=0) as mock_stop:
            result = manager.execute("stop")
            mock_stop.assert_called_once()
            assert result == 0

    def test_execute_restart_dispatches(self):
        """UT-DAEMON-005: execute('restart') dispatches to restart()."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'restart', return_value=0) as mock_restart:
            result = manager.execute("restart")
            mock_restart.assert_called_once()
            assert result == 0

    def test_execute_status_dispatches(self):
        """UT-DAEMON-006: execute('status') dispatches to status()."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.shared.src.taxonomy_daemon_vo import DaemonStatus

        manager = AnytypeDaemonManager()
        expected_status = DaemonStatus(
            container_state="running",
            service_state="active",
            api_ready=True,
            data_dir="/test",
            ok=True,
        )
        with patch.object(manager, 'status', return_value=expected_status):
            result = manager.execute("status")
            assert result == expected_status

    def test_execute_logs_dispatches(self):
        """UT-DAEMON-007: execute('logs') dispatches to logs()."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'logs', return_value=0) as mock_logs:
            result = manager.execute("logs")
            mock_logs.assert_called_once()
            assert result == 0

    def test_execute_install_unit_dispatches(self):
        """UT-DAEMON-008: execute('install_unit') dispatches to install_unit()."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'install_unit', return_value=0) as mock_install:
            result = manager.execute("install_unit")
            mock_install.assert_called_once()
            assert result == 0

    def test_execute_remove_unit_dispatches(self):
        """UT-DAEMON-009: execute('remove_unit') dispatches to remove_unit()."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'remove_unit', return_value=0) as mock_remove:
            result = manager.execute("remove_unit")
            mock_remove.assert_called_once()
            assert result == 0

    def test_execute_unit_status_dispatches(self):
        """UT-DAEMON-010: execute('unit_status') dispatches to unit_status()."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'unit_status', return_value=0) as mock_unit:
            result = manager.execute("unit_status")
            mock_unit.assert_called_once()
            assert result == 0

    def test_execute_auth_create_dispatches(self):
        """UT-DAEMON-011: execute('auth-create') dispatches to auth_create()."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'auth_create', return_value=0) as mock_auth:
            result = manager.execute("auth-create", name="test-agent")
            mock_auth.assert_called_once_with("test-agent")
            assert result == 0

    def test_execute_auth_key_dispatches(self):
        """UT-DAEMON-012: execute('auth-key') dispatches to auth_key()."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'auth_key', return_value=0) as mock_key:
            result = manager.execute("auth-key", name="my-key")
            mock_key.assert_called_once_with("my-key")
            assert result == 0

    def test_execute_space_join_dispatches(self):
        """UT-DAEMON-013: execute('space-join') dispatches to space_join()."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'space_join', return_value=0) as mock_join:
            result = manager.execute("space-join", name="invite-link")
            mock_join.assert_called_once_with("invite-link")
            assert result == 0

    def test_execute_space_list_dispatches(self):
        """UT-DAEMON-014: execute('space-list') dispatches to space_list()."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'space_list', return_value=0) as mock_list:
            result = manager.execute("space-list")
            mock_list.assert_called_once()
            assert result == 0

    def test_execute_help_dispatches(self):
        """UT-DAEMON-015: execute('help') dispatches to help()."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'help', return_value=0) as mock_help:
            result = manager.execute("help")
            mock_help.assert_called_once()
            assert result == 0

    def test_execute_unknown_op_raises(self):
        """UT-DAEMON-016: execute raises ValueError for unknown op."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        try:
            manager.execute("nonexistent-op")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unknown daemon op: nonexistent-op" in str(e)


class TestPodmanDaemonManagerInit:
    """Tests for PodmanDaemonManager initialization."""

    def test_init_default_params(self):
        """UT-DAEMON-017: PodmanDaemonManager initializes with default params."""
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        manager = PodmanDaemonManager()
        assert repr(manager) == "PodmanDaemonManager()"

    def test_init_with_params(self):
        """UT-DAEMON-018: PodmanDaemonManager accepts root and daemons."""
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        manager = PodmanDaemonManager(root=Path("/test"), daemons=None)
        assert manager is not None


class TestPodmanExecuteDispatch:
    """Tests for PodmanDaemonManager.execute dispatching."""

    def test_execute_start_dispatches(self):
        """UT-DAEMON-019: execute('start') dispatches to start()."""
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        manager = PodmanDaemonManager()
        with patch.object(manager, 'start', return_value=0) as mock_start:
            result = manager.execute("start")
            mock_start.assert_called_once()
            assert result == 0

    def test_execute_stop_dispatches(self):
        """UT-DAEMON-020: execute('stop') dispatches to stop()."""
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        manager = PodmanDaemonManager()
        with patch.object(manager, 'stop', return_value=0) as mock_stop:
            result = manager.execute("stop")
            mock_stop.assert_called_once()
            assert result == 0

    def test_execute_restart_dispatches(self):
        """UT-DAEMON-021: execute('restart') dispatches to restart()."""
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        manager = PodmanDaemonManager()
        with patch.object(manager, 'restart', return_value=0) as mock_restart:
            result = manager.execute("restart")
            mock_restart.assert_called_once()
            assert result == 0

    def test_execute_status_dispatches(self):
        """UT-DAEMON-022: execute('status') dispatches to status()."""
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager
        from modules.shared.src.taxonomy_daemon_vo import DaemonStatus

        manager = PodmanDaemonManager()
        expected_status = DaemonStatus(
            container_state="running",
            service_state="active",
            api_ready=True,
            data_dir="/test",
            ok=True,
        )
        with patch.object(manager, 'status', return_value=expected_status):
            result = manager.execute("status")
            assert result == expected_status

    def test_execute_logs_dispatches(self):
        """UT-DAEMON-023: execute('logs') dispatches to logs()."""
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        manager = PodmanDaemonManager()
        with patch.object(manager, 'logs', return_value=0) as mock_logs:
            result = manager.execute("logs")
            mock_logs.assert_called_once()
            assert result == 0

    def test_execute_models_dispatches(self):
        """UT-DAEMON-024: execute('models') dispatches to models()."""
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        manager = PodmanDaemonManager()
        with patch.object(manager, 'models', return_value=0) as mock_models:
            result = manager.execute("models")
            mock_models.assert_called_once()
            assert result == 0

    def test_execute_install_unit_dispatches(self):
        """UT-DAEMON-025: execute('install_unit') dispatches to install_unit()."""
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        manager = PodmanDaemonManager()
        with patch.object(manager, 'install_unit', return_value=0) as mock_install:
            result = manager.execute("install_unit")
            mock_install.assert_called_once()
            assert result == 0

    def test_execute_remove_unit_dispatches(self):
        """UT-DAEMON-026: execute('remove_unit') dispatches to remove_unit()."""
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        manager = PodmanDaemonManager()
        with patch.object(manager, 'remove_unit', return_value=0) as mock_remove:
            result = manager.execute("remove_unit")
            mock_remove.assert_called_once()
            assert result == 0

    def test_execute_unit_status_dispatches(self):
        """UT-DAEMON-027: execute('unit_status') dispatches to unit_status()."""
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        manager = PodmanDaemonManager()
        with patch.object(manager, 'unit_status', return_value=0) as mock_unit:
            result = manager.execute("unit_status")
            mock_unit.assert_called_once()
            assert result == 0

    def test_execute_help_dispatches(self):
        """UT-DAEMON-028: execute('help') dispatches to help()."""
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        manager = PodmanDaemonManager()
        with patch.object(manager, 'help', return_value=0) as mock_help:
            result = manager.execute("help")
            mock_help.assert_called_once()
            assert result == 0

    def test_execute_unknown_op_raises(self):
        """UT-DAEMON-029: execute raises ValueError for unknown op."""
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        manager = PodmanDaemonManager()
        try:
            manager.execute("nonexistent-op")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unknown daemon op: nonexistent-op" in str(e)


class TestHelperFunctions:
    """Tests for helper functions in capabilities_anytype_daemon."""

    def test_api_ready_returns_bool(self):
        """UT-DAEMON-030: api_ready function exists and is callable."""
        from modules.daemon.src.capabilities_anytype_daemon import api_ready
        # Verify function exists (actual call skipped due to network dependency)
        assert callable(api_ready)

    def test_container_running_checks_podman(self):
        """UT-DAEMON-031: container_running checks podman state."""
        from modules.daemon.src.capabilities_anytype_daemon import container_running

        with patch('modules.daemon.src.capabilities_anytype_daemon.out', return_value="true"):
            result = container_running()
            assert result is True

        with patch('modules.daemon.src.capabilities_anytype_daemon.out', return_value="false"):
            result = container_running()
            assert result is False

    def test_container_exists_checks_podman(self):
        """UT-DAEMON-032: container_exists checks podman container."""
        from modules.daemon.src.capabilities_anytype_daemon import container_exists, CONTAINER_NAME

        with patch('modules.daemon.src.capabilities_anytype_daemon.out', return_value=CONTAINER_NAME):
            result = container_exists()
            assert result is True

        with patch('modules.daemon.src.capabilities_anytype_daemon.out', return_value=""):
            result = container_exists()
            assert result is False

    def test_extract_api_key_finds_token(self):
        """UT-DAEMON-033: _extract_api_key finds token-shaped key."""
        from modules.daemon.src.capabilities_anytype_daemon import _extract_api_key

        stdout = "Some text\nABCdef1234567890xyz_more_text\nMore text"
        result = _extract_api_key(stdout)
        assert result == "ABCdef1234567890xyz_more_text"

    def test_extract_api_key_fallback_to_last_line(self):
        """UT-DAEMON-034: _extract_api_key falls back to last line."""
        from modules.daemon.src.capabilities_anytype_daemon import _extract_api_key

        stdout = "No tokens here\nJust a regular line"
        result = _extract_api_key(stdout)
        assert result == "Just a regular line"

    def test_extract_api_key_empty_output(self):
        """UT-DAEMON-035: _extract_api_key handles empty output."""
        from modules.daemon.src.capabilities_anytype_daemon import _extract_api_key

        result = _extract_api_key("")
        assert result == ""

    def test_has_podman_returns_bool(self):
        """UT-DAEMON-036: has_podman returns boolean."""
        from modules.daemon.src.capabilities_anytype_daemon import has_podman

        with patch('modules.daemon.src.capabilities_anytype_daemon.shutil.which', return_value="/usr/bin/podman"):
            assert has_podman() is True

        with patch('modules.daemon.src.capabilities_anytype_daemon.shutil.which', return_value=None):
            assert has_podman() is False

    def test_image_exists_checks_podman(self):
        """UT-DAEMON-037: image_exists checks podman image."""
        from modules.daemon.src.capabilities_anytype_daemon import image_exists

        with patch('modules.daemon.src.capabilities_anytype_daemon.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = image_exists()
            assert result is True

        with patch('modules.daemon.src.capabilities_anytype_daemon.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = image_exists()
            assert result is False


class TestDaemonOrchestrator:
    """Tests for DaemonOrchestrator routing logic."""

    def test_init_stores_managers(self):
        """UT-DAEMON-038: DaemonOrchestrator stores both managers."""
        from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        omniroute = PodmanDaemonManager()
        anytype = AnytypeDaemonManager()
        orchestrator = DaemonOrchestrator(omniroute, anytype)
        assert orchestrator._omniroute is omniroute
        assert orchestrator._anytype is anytype
        assert "omniroute" in orchestrator._managers
        assert "anytype" in orchestrator._managers

    def test_list_known_returns_tuple(self):
        """UT-DAEMON-039: list_known returns tuple of DaemonNames."""
        from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        omniroute = PodmanDaemonManager()
        anytype = AnytypeDaemonManager()
        orchestrator = DaemonOrchestrator(omniroute, anytype)

        result = orchestrator.list_known()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert str(result[0]) == "omniroute"
        assert str(result[1]) == "anytype"

    def test_start_routes_to_manager(self):
        """UT-DAEMON-040: start routes to correct manager."""
        from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator, DaemonName
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        omniroute = PodmanDaemonManager()
        anytype = AnytypeDaemonManager()
        orchestrator = DaemonOrchestrator(omniroute, anytype)

        with patch.object(anytype, 'execute', return_value=0) as mock_exec:
            result = orchestrator.start(DaemonName("anytype"))
            mock_exec.assert_called_once_with("start")
            assert result == 0

    def test_stop_routes_to_manager(self):
        """UT-DAEMON-041: stop routes to correct manager."""
        from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator, DaemonName
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        omniroute = PodmanDaemonManager()
        anytype = AnytypeDaemonManager()
        orchestrator = DaemonOrchestrator(omniroute, anytype)

        with patch.object(omniroute, 'execute', return_value=0) as mock_exec:
            result = orchestrator.stop(DaemonName("omniroute"))
            mock_exec.assert_called_once_with("stop")
            assert result == 0

    def test_status_routes_and_validates(self):
        """UT-DAEMON-042: status routes and validates DaemonStatus return."""
        from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator, DaemonName
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager
        from modules.shared.src.taxonomy_daemon_vo import DaemonStatus

        omniroute = PodmanDaemonManager()
        anytype = AnytypeDaemonManager()
        orchestrator = DaemonOrchestrator(omniroute, anytype)

        expected = DaemonStatus(
            container_state="running",
            service_state="active",
            api_ready=True,
            data_dir="/test",
            ok=True,
        )
        with patch.object(anytype, 'execute', return_value=expected):
            result = orchestrator.status(DaemonName("anytype"))
            assert result == expected

    def test_unknown_daemon_raises(self):
        """UT-DAEMON-043: start raises ValueError for unknown daemon."""
        from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator, DaemonName
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        omniroute = PodmanDaemonManager()
        anytype = AnytypeDaemonManager()
        orchestrator = DaemonOrchestrator(omniroute, anytype)

        try:
            orchestrator.start(DaemonName("unknown-daemon"))
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unknown daemon: unknown-daemon" in str(e)

    def test_for_unit_resolves_by_service_suffix(self):
        """UT-DAEMON-044: _for_unit resolves by .service suffix."""
        from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        omniroute = PodmanDaemonManager()
        anytype = AnytypeDaemonManager()
        orchestrator = DaemonOrchestrator(omniroute, anytype)

        result = orchestrator._for_unit("anytype-daemon.service")
        assert result is anytype

    def test_for_unit_resolves_by_name(self):
        """UT-DAEMON-045: _for_unit resolves by daemon name without suffix."""
        from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        omniroute = PodmanDaemonManager()
        anytype = AnytypeDaemonManager()
        orchestrator = DaemonOrchestrator(omniroute, anytype)

        result = orchestrator._for_unit("omniroute")
        assert result is omniroute

    def test_for_unit_unknown_raises(self):
        """UT-DAEMON-046: _for_unit raises for unknown unit."""
        from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        omniroute = PodmanDaemonManager()
        anytype = AnytypeDaemonManager()
        orchestrator = DaemonOrchestrator(omniroute, anytype)

        try:
            orchestrator._for_unit("unknown.service")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unknown unit: unknown.service" in str(e)

    def test_repr(self):
        """UT-DAEMON-047: DaemonOrchestrator repr is descriptive."""
        from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

        omniroute = PodmanDaemonManager()
        anytype = AnytypeDaemonManager()
        orchestrator = DaemonOrchestrator(omniroute, anytype)

        assert repr(orchestrator) == "DaemonOrchestrator()"
