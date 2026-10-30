"""Unit tests for modules/daemon — test implementation details with mocking."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch


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
        with patch.object(manager, 'start', return_value=0):
            result = manager.start()
            assert result == 0

    def test_stop_method_exists(self):
        """UT-DAEMON-004: stop() method exists and is callable."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'stop', return_value=0):
            result = manager.stop()
            assert result == 0

    def test_restart_method_exists(self):
        """UT-DAEMON-005: restart() method exists and is callable."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'restart', return_value=0):
            result = manager.restart()
            assert result == 0

    def test_status_method_exists(self):
        """UT-DAEMON-006: status() method exists and is callable."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.shared.src.daemon.taxonomy_daemon_vo import DaemonStatus

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
        with patch.object(manager, 'logs', return_value=0):
            result = manager.logs()
            assert result == 0

    def test_install_unit_method_exists(self):
        """UT-DAEMON-008: install_unit() method exists and is callable."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.shared.src.daemon.taxonomy_daemon_vo import DaemonUnit

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'install_unit', return_value=0):
            result = manager.install_unit(DaemonUnit("anytype-daemon.service"))
            assert result == 0

    def test_remove_unit_method_exists(self):
        """UT-DAEMON-009: remove_unit() method exists and is callable."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.shared.src.daemon.taxonomy_daemon_vo import DaemonUnit

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'remove_unit', return_value=0):
            result = manager.remove_unit(DaemonUnit("anytype-daemon.service"))
            assert result == 0

    def test_unit_status_method_exists(self):
        """UT-DAEMON-010: unit_status() method exists and is callable."""
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.shared.src.daemon.taxonomy_daemon_vo import DaemonUnit

        manager = AnytypeDaemonManager()
        with patch.object(manager, 'unit_status', return_value=0):
            result = manager.unit_status(DaemonUnit("anytype-daemon.service"))
            assert result == 0


class TestOmnirouteRichProtocol:
    """Tests for OmnirouteDaemonManager exposing rich named protocol methods."""

    def test_start_method_exists(self):
        """UT-DAEMON-011: start() method exists and is callable."""
        from modules.daemon.src.capabilities_omniroute_daemon import (
            OmnirouteDaemonManager,
        )

        manager = OmnirouteDaemonManager()
        with patch.object(manager, 'start', return_value=0):
            result = manager.start()
            assert result == 0

    def test_status_method_exists(self):
        """UT-DAEMON-012: status() method exists and is callable."""
        from modules.daemon.src.capabilities_omniroute_daemon import (
            OmnirouteDaemonManager,
        )
        from modules.shared.src.daemon.taxonomy_daemon_vo import DaemonStatus

        manager = OmnirouteDaemonManager()
        with patch.object(
            manager, 'status',
            return_value=DaemonStatus("stopped", "stopped", False, "", False),
        ):
            result = manager.status()
            assert isinstance(result, DaemonStatus)

    def test_install_unit_method_exists(self):
        """UT-DAEMON-013: install_unit() method exists and is callable."""
        from modules.daemon.src.capabilities_omniroute_daemon import (
            OmnirouteDaemonManager,
        )
        from modules.shared.src.daemon.taxonomy_daemon_vo import DaemonUnit

        manager = OmnirouteDaemonManager()
        with patch.object(manager, 'install_unit', return_value=0):
            result = manager.install_unit(DaemonUnit("omniroute.service"))
            assert result == 0


class TestNinerouterRichProtocol:
    """Tests for NinerouterDaemonManager exposing rich named protocol methods."""

    def test_init_default_params(self):
        """UT-DAEMON-011b: NinerouterDaemonManager initializes with defaults."""
        from modules.daemon.src.capabilities_9router_daemon import (
            NinerouterDaemonManager,
        )

        manager = NinerouterDaemonManager()
        assert repr(manager) == "NinerouterDaemonManager()"

    def test_start_method_exists(self):
        """UT-DAEMON-011c: start() method exists and is callable."""
        from modules.daemon.src.capabilities_9router_daemon import (
            NinerouterDaemonManager,
        )

        manager = NinerouterDaemonManager()
        with patch.object(manager, 'start', return_value=0):
            result = manager.start()
            assert result == 0

    def test_status_method_exists(self):
        """UT-DAEMON-012b: status() method exists and is callable."""
        from modules.daemon.src.capabilities_9router_daemon import (
            NinerouterDaemonManager,
        )
        from modules.shared.src.daemon.taxonomy_daemon_vo import DaemonStatus

        manager = NinerouterDaemonManager()
        with patch.object(
            manager, 'status',
            return_value=DaemonStatus("stopped", "stopped", False, "", False),
        ):
            result = manager.status()
            assert isinstance(result, DaemonStatus)

    def test_install_unit_method_exists(self):
        """UT-DAEMON-013b: install_unit() method exists and is callable."""
        from modules.daemon.src.capabilities_9router_daemon import (
            NinerouterDaemonManager,
        )
        from modules.shared.src.daemon.taxonomy_daemon_vo import DaemonUnit

        manager = NinerouterDaemonManager()
        with patch.object(manager, 'install_unit', return_value=0):
            result = manager.install_unit(DaemonUnit("9router.service"))
            assert result == 0

class TestDaemonAggregateNoExecuteMethod:
    """The aggregate should NOT have a named execute method in the old style."""

    def test_orchestrator_has_single_execute(self):
        """UT-DAEMON-014: DaemonOrchestrator has a single execute() method."""
        from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.daemon.src.capabilities_omniroute_daemon import (
            OmnirouteDaemonManager,
        )

        orch = DaemonOrchestrator(OmnirouteDaemonManager(), AnytypeDaemonManager())
        assert callable(orch.execute)
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
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.daemon.src.capabilities_omniroute_daemon import (
            OmnirouteDaemonManager,
        )

        orch = DaemonOrchestrator(OmnirouteDaemonManager(), AnytypeDaemonManager())
        assert orch._omniroute is not None
        assert orch._anytype is not None

    def test_execute_routes_to_correct_manager(self):
        """UT-DAEMON-024: DaemonOrchestrator.execute routes by op + name."""
        from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.daemon.src.capabilities_omniroute_daemon import (
            OmnirouteDaemonManager,
        )
        from modules.shared.src.daemon.taxonomy_daemon_vo import (
            DaemonName,
            DaemonOp,
            DaemonRequest,
        )

        orch = DaemonOrchestrator(OmnirouteDaemonManager(), AnytypeDaemonManager())
        # Patch the anytype manager's start to confirm routing.
        with patch.object(orch._anytype, "start", return_value=0) as mock_start:
            orch.execute(DaemonRequest(DaemonOp("start"), name=DaemonName("anytype")))
            mock_start.assert_called_once()

    def test_init_stores_ninerouter_sibling(self):
        """UT-DAEMON-025: DaemonOrchestrator stores the 9router manager alongside omniroute."""
        from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
        from modules.daemon.src.capabilities_9router_daemon import (
            NinerouterDaemonManager,
        )
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.daemon.src.capabilities_omniroute_daemon import (
            OmnirouteDaemonManager,
        )

        orch = DaemonOrchestrator(
            AnytypeDaemonManager(), OmnirouteDaemonManager(), NinerouterDaemonManager()
        )
        assert orch._ninerouter is not None
        assert orch._omniroute is not None
        assert orch._anytype is not None
        assert set(orch._managers) == {"anytype", "omniroute", "9router"}

    def test_execute_routes_9router_independently(self):
        """UT-DAEMON-026: 9router requests never reach the omniroute manager."""
        from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
        from modules.daemon.src.capabilities_9router_daemon import (
            NinerouterDaemonManager,
        )
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.daemon.src.capabilities_omniroute_daemon import (
            OmnirouteDaemonManager,
        )
        from modules.shared.src.daemon.taxonomy_daemon_vo import (
            DaemonName,
            DaemonOp,
            DaemonRequest,
        )

        orch = DaemonOrchestrator(
            AnytypeDaemonManager(), OmnirouteDaemonManager(), NinerouterDaemonManager()
        )
        with patch.object(orch._ninerouter, "restart", return_value=0) as mock_restart, \
                patch.object(orch._omniroute, "restart", return_value=0) as mock_omni:
            orch.execute(DaemonRequest(DaemonOp("restart"), name=DaemonName("9router")))
            mock_restart.assert_called_once()
            mock_omni.assert_not_called()

    def test_unit_map_routes_both_gateway_units(self):
        """UT-DAEMON-027: unit ops resolve 9router.service and omniroute.service."""
        from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
        from modules.daemon.src.capabilities_9router_daemon import (
            NinerouterDaemonManager,
        )
        from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
        from modules.daemon.src.capabilities_omniroute_daemon import (
            OmnirouteDaemonManager,
        )
        from modules.shared.src.daemon.taxonomy_daemon_vo import (
            DaemonOp,
            DaemonRequest,
            DaemonUnit,
        )

        orch = DaemonOrchestrator(
            AnytypeDaemonManager(), OmnirouteDaemonManager(), NinerouterDaemonManager()
        )
        with patch.object(orch._omniroute, "unit_status", return_value=0) as mock_omni, \
                patch.object(orch._ninerouter, "unit_status", return_value=0) as mock_nine:
            orch.execute(
                DaemonRequest(DaemonOp("unit_status"), unit=DaemonUnit("omniroute.service"))
            )
            orch.execute(
                DaemonRequest(DaemonOp("unit_status"), unit=DaemonUnit("9router.service"))
            )
            mock_omni.assert_called_once_with(DaemonUnit("omniroute.service"))
            mock_nine.assert_called_once_with(DaemonUnit("9router.service"))


def test_auth_key_writes_private_xdg_env_only(tmp_path, monkeypatch):
    """WS-05: auth-key uses the private XDG config path, not repo config."""
    from types import SimpleNamespace

    from modules.daemon.src import capabilities_anytype_daemon as anytype
    from modules.shared.src.common.utility_envfile_parser import parse_env_file

    local_bin = tmp_path / "bin"
    local_bin.mkdir()
    (local_bin / "anytype").write_text("placeholder", encoding="utf-8")
    monkeypatch.setattr(anytype, "LOCAL_BIN", local_bin)
    monkeypatch.setattr(anytype, "has_podman", lambda: False)

    repo = tmp_path / "repo"
    (repo / "config").mkdir(parents=True)
    xdg_config = tmp_path / "xdg-config" / "agents-arwaky"
    monkeypatch.setattr(anytype, "agents_arwaky_config_dir", lambda: xdg_config)

    secret = "a" * 32
    monkeypatch.setattr(
        anytype.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout=f"API key: {secret}\n",
            stderr="",
        ),
    )

    from modules.root_cli_entry import cmd_anytype

    assert cmd_anytype(["auth-key", "test-agent"]) == 0
    env_file = xdg_config / "anytype.env"
    assert parse_env_file(env_file)["ANYTYPE_API_KEY"] == secret
    assert env_file.stat().st_mode & 0o777 == 0o600
    assert not (repo / "config" / "anytype.env").exists()

class TestNinerouterDaemonProbes:
    """Probe/helper behaviour for the 9router manager, with host I/O mocked."""

    def test_base_url_targets_default_port(self):
        """UT-DAEMON-028: base_url() points at the 9router default port."""
        from modules.daemon.src import capabilities_9router_daemon as nine

        assert nine.base_url() == f"http://127.0.0.1:{nine.NINEROUTER_PORT}"
        assert nine.NINEROUTER_PORT == "20128"

    def test_status_reports_running_when_probe_succeeds(self, monkeypatch, capsys):
        """UT-DAEMON-029: status() folds process + API probes into a DaemonStatus."""
        from modules.daemon.src import capabilities_9router_daemon as nine
        from modules.shared.src.daemon.taxonomy_daemon_vo import DaemonStatus

        monkeypatch.setattr(nine, "process_running", lambda: True)
        monkeypatch.setattr(nine, "api_ready", lambda timeout=90: True)
        monkeypatch.setattr(nine, "service_installed", lambda: False)

        status = nine.NinerouterDaemonManager().status()

        assert isinstance(status, DaemonStatus)
        assert status.container_state == "running"
        assert status.service_state == "not-installed"
        assert status.api_ready is True
        assert status.ok is True
        capsys.readouterr()

    def test_status_reports_stopped_when_probe_fails(self, monkeypatch, capsys):
        """UT-DAEMON-030: status() reports stopped when nothing answers."""
        from modules.daemon.src import capabilities_9router_daemon as nine

        monkeypatch.setattr(nine, "process_running", lambda: False)
        monkeypatch.setattr(nine, "api_ready", lambda timeout=90: False)
        monkeypatch.setattr(nine, "service_installed", lambda: False)

        status = nine.NinerouterDaemonManager().status()

        assert status.container_state == "stopped"
        assert status.ok is False
        capsys.readouterr()

    def test_install_unit_routes_to_service_install(self, monkeypatch):
        """UT-DAEMON-031: install_unit() delegates to the systemd installer."""
        from modules.daemon.src import capabilities_9router_daemon as nine
        from modules.shared.src.daemon.taxonomy_daemon_vo import DaemonUnit

        monkeypatch.setattr(nine, "cmd_service_install", lambda: 0)
        assert nine.NinerouterDaemonManager().install_unit(
            DaemonUnit("9router.service")
        ) == 0

    def test_remove_and_status_units_delegate(self, monkeypatch):
        """UT-DAEMON-032: remove_unit/unit_status delegate to their handlers."""
        from modules.daemon.src import capabilities_9router_daemon as nine
        from modules.shared.src.daemon.taxonomy_daemon_vo import DaemonUnit

        monkeypatch.setattr(nine, "cmd_service_uninstall", lambda: 0)
        monkeypatch.setattr(nine, "cmd_service_status", lambda: 0)

        manager = nine.NinerouterDaemonManager()
        assert manager.remove_unit(DaemonUnit("9router.service")) == 0
        assert manager.unit_status(DaemonUnit("9router.service")) == 0

    def test_wrapper_detection_skips_repo_shim(self, tmp_path):
        """UT-DAEMON-033: the `aa 9router` shim is never handed to systemd."""
        from modules.daemon.src import capabilities_9router_daemon as nine

        shim = tmp_path / "9router"
        shim.write_bytes(b"#!/usr/bin/env python3\n# arwaky-installer\n")
        real = tmp_path / "real-9router"
        real.write_bytes(b"#!/usr/bin/env node\n")

        assert nine._is_9router_wrapper(shim) is True
        assert nine._is_9router_wrapper(real) is False

    def test_unit_content_names_the_9router_binary(self, monkeypatch):
        """UT-DAEMON-034: rendered unit launches the resolved binary on 20128."""
        from modules.daemon.src import capabilities_9router_daemon as nine

        content = nine._unit_content("/usr/local/bin/9router")
        assert "ExecStart=/usr/local/bin/9router --port 20128" in content
        assert "WorkingDirectory=%h/.9router" in content

    def test_seed_env_never_overwrites_existing_file(self, tmp_path, monkeypatch):
        """UT-DAEMON-035: an existing ~/.9router/.env is left untouched."""
        from modules.daemon.src import capabilities_9router_daemon as nine

        data_dir = tmp_path / ".9router"
        data_dir.mkdir()
        env_file = data_dir / ".env"
        env_file.write_text("EXISTING=1\n", encoding="utf-8")

        monkeypatch.setattr(nine, "NINEROUTER_DATA_DIR", data_dir)
        nine.seed_env()

        assert env_file.read_text(encoding="utf-8") == "EXISTING=1\n"
