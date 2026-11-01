"""Unit tests for modules/daemon — test implementation details with mocking."""
from __future__ import annotations

import hashlib
import sqlite3
from os import urandom as os_urandom
from pathlib import Path
from unittest.mock import patch

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


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


class TestImportOmniroute:
    """Unit tests for `capabilities_9router_import_omniroute` using temp SQLite fixtures."""

    @staticmethod
    def _encrypt(plain: str, secret: str) -> str:
        """Encrypt *plain* with the OmniRoute scheme (static salt) for fixture building."""
        key = hashlib.scrypt(
            secret.encode(),
            salt=b"omniroute-field-encryption-v1",
            dklen=32,
            n=16384,
            r=8,
            p=1,
        )
        iv = os_urandom(16)
        ct = AESGCM(key).encrypt(iv, plain.encode(), None)
        tag = ct[-16:]
        body = ct[:-16]
        return "enc:v1:" + iv.hex() + ":" + body.hex() + ":" + tag.hex()

    @staticmethod
    def _make_omni_db(tmp_path: Path, secret: str) -> Path:
        db = tmp_path / "omni.sqlite"
        conn = sqlite3.connect(db)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS provider_connections("
            "id TEXT PRIMARY KEY, provider TEXT, auth_type TEXT, name TEXT, email TEXT, "
            "priority INTEGER, is_active INTEGER, api_key TEXT, access_token TEXT, "
            "refresh_token TEXT, id_token TEXT, expires_at TEXT, token_expires_at TEXT, "
            "scope TEXT, project_id TEXT, display_name TEXT, default_model TEXT, "
            "token_type TEXT, expires_in TEXT, provider_specific_data TEXT, "
            "created_at TEXT, updated_at TEXT, \"group\" TEXT, max_concurrent INTEGER, "
            "global_priority INTEGER)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS provider_nodes("
            "id TEXT PRIMARY KEY, type TEXT, name TEXT, prefix TEXT, api_type TEXT, "
            "base_url TEXT, chat_path TEXT, models_path TEXT, custom_headers_json TEXT)"
        )
        cols = [
            "id", "provider", "auth_type", "name", "email", "priority", "is_active",
            "api_key", "access_token", "refresh_token", "id_token", "expires_at",
            "token_expires_at", "scope", "project_id", "display_name", "default_model",
            "token_type", "expires_in", "provider_specific_data", "created_at",
            "updated_at", '"group"', "max_concurrent", "global_priority",
        ]
        placeholders = ", ".join(["?"] * len(cols))

        def row(**kw):
            base = {c: None for c in cols}
            base.update(kw)
            return tuple(base[c] for c in cols)

        conn.execute("DELETE FROM provider_connections")
        conn.execute("DELETE FROM provider_nodes")

        # apikey row
        conn.execute(
            f"INSERT INTO provider_connections({', '.join(cols)}) VALUES({placeholders})",
            row(
                id="c-apikey-1", provider="openrouter", auth_type="apikey",
                name="openrouter-main", email="o@e.com", priority=1, is_active=1,
                api_key=TestImportOmniroute._encrypt("sk-or-v1-1111", secret),
                provider_specific_data='{"extra":"x"}',
                created_at="2026-01-01T00:00:00Z", updated_at="2026-01-02T00:00:00Z",
            ),
        )
        # oauth row with all secrets
        conn.execute(
            f"INSERT INTO provider_connections({', '.join(cols)}) VALUES({placeholders})",
            row(
                id="c-oauth-1", provider="agy", auth_type="oauth",
                name="arwaky001@gmail.com", email="arwaky001@gmail.com", priority=2,
                is_active=1, access_token=TestImportOmniroute._encrypt("ya29.access", secret),
                refresh_token=TestImportOmniroute._encrypt("ya29.refresh", secret),
                id_token=TestImportOmniroute._encrypt("ya29.id", secret),
                expires_at="2026-10-30T08:25:23Z", token_expires_at="2026-10-30T08:25:23Z",
                scope="openid email", project_id="proj-x", expires_in="3599",
                provider_specific_data='{"nodeName":"agy"}',
                created_at="2026-09-01T00:00:00Z", updated_at="2026-10-01T00:00:00Z",
            ),
        )
        # oauth row whose access_token FAILS to decrypt (undecryptable ciphertext)
        conn.execute(
            f"INSERT INTO provider_connections({', '.join(cols)}) VALUES({placeholders})",
            row(
                id="c-oauth-fail", provider="agy", auth_type="oauth",
                name="arwaky002@gmail.com", email="arwaky002@gmail.com", priority=3,
                is_active=1,
                access_token="enc:v1:" + "00" * 16 + ":deadbeef:cafebabe",
                created_at="2026-09-01T00:00:00Z", updated_at="2026-10-01T00:00:00Z",
            ),
        )
        # apikey node referenced by an openai-compatible-chat-* provider
        conn.execute(
            "INSERT INTO provider_nodes VALUES(?,?,?,?,?,?,?,?,?)",
            ["openai-compatible-chat-node1", "openai-compatible", "tokenharbor.ai", "tokenharbor", "chat",
             "https://tokenharbor.ai/v1", "/v1/chat/completions", "/v1/models", None],
        )
        conn.execute(
            f"INSERT INTO provider_connections({', '.join(cols)}) VALUES({placeholders})",
            row(
                id="c-openai-comp", provider="openai-compatible-chat-node1", auth_type="apikey",
                name="tokenharbor", email="o@e.com", priority=4, is_active=1,
                api_key=TestImportOmniroute._encrypt("sk-comp-2222", secret),
                created_at="2026-02-01T00:00:00Z", updated_at="2026-02-02T00:00:00Z",
            ),
        )
        conn.commit()
        conn.close()
        return db

    def _run_plan(self, tmp_path, secret="test-secret-xyz", providers=None):
        from modules.daemon.src.capabilities_9router_import_omniroute import (
            load_omniroute_connections,
            load_omniroute_nodes,
            plan_import,
        )
        db = self._make_omni_db(tmp_path, secret)
        conns = load_omniroute_connections(db, secret=secret)
        nodes = load_omniroute_nodes(db)
        plan = plan_import(conns, nodes, providers=providers)
        return conns, nodes, plan, db

    def test_decrypt_field_apikey(self, tmp_path):
        from modules.daemon.src.capabilities_9router_import_omniroute import (
            load_omniroute_connections,
        )
        db = self._make_omni_db(tmp_path, "test-secret-xyz")
        conns = load_omniroute_connections(db, secret="test-secret-xyz")
        apikey = next(c for c in conns if c["id"] == "c-apikey-1")
        assert apikey["api_key"] == "sk-or-v1-1111"
        oauth = next(c for c in conns if c["id"] == "c-oauth-1")
        assert oauth["access_token"] == "ya29.access"
        assert oauth["refresh_token"] == "ya29.refresh"
        assert oauth["id_token"] == "ya29.id"
        fail = next(c for c in conns if c["id"] == "c-oauth-fail")
        assert fail["access_token"] is None  # undecryptable -> None

    def test_map_connection_shapes(self, tmp_path):
        from modules.daemon.src.capabilities_9router_import_omniroute import (
            load_omniroute_connections,
            load_omniroute_nodes,
            map_connection_to_9router,
        )
        db = self._make_omni_db(tmp_path, "test-secret-xyz")
        conns = load_omniroute_connections(db, secret="test-secret-xyz")
        nodes = load_omniroute_nodes(db)
        item = map_connection_to_9router(conns[0], nodes)
        assert item["id"] == "c-apikey-1"
        assert item["provider"] == "openrouter"
        assert item["authType"] == "apikey"
        assert item["isActive"] == 1
        assert item["data"]["apiKey"] == "sk-or-v1-1111"
        assert item["data"]["providerSpecificData"] == {"extra": "x"}
        # openai-compatible node picked up
        comp = next(c for c in conns if c["id"] == "c-openai-comp")
        item2 = map_connection_to_9router(comp, nodes)
        assert item2["data"]["providerNode"]["baseUrl"] == "https://tokenharbor.ai/v1"
        assert item2["data"]["providerNode"]["apiType"] == "chat"

    def test_dry_run_plan_counts(self, tmp_path):
        _, _, plan, _db = self._run_plan(tmp_path)
        assert plan["total"] == 4
        assert plan["apikey"] == 2
        assert plan["oauth"] == 2
        assert plan["decrypt_failures"] == 1
        assert plan["would_import"] == 4
        assert plan["would_skip_existing"] == 0
        # provider filter
        _, _, plan2, _db2 = self._run_plan(tmp_path, providers=["agy"])
        assert plan2["total"] == 2
        assert plan2["would_skip_provider_filter"] == 2

    def test_dedupe_skip_existing(self, tmp_path):
        from modules.daemon.src.capabilities_9router_import_omniroute import (
            load_omniroute_connections,
            load_omniroute_nodes,
            plan_import,
        )
        db = self._make_omni_db(tmp_path, "test-secret-xyz")
        conns = load_omniroute_connections(db, secret="test-secret-xyz")
        nodes = load_omniroute_nodes(db)
        plan = plan_import(conns, nodes, existing_ids={"c-apikey-1"})
        skipped = [i for i in plan["items"] if i.get("skip")]
        assert len(skipped) == 1
        assert skipped[0]["id"] == "c-apikey-1"
        assert plan["would_skip_existing"] == 1
        assert plan["would_import"] == 3

    def test_dedupe_by_api_key(self, tmp_path):
        from modules.daemon.src.capabilities_9router_import_omniroute import (
            load_omniroute_connections,
            load_omniroute_nodes,
            plan_import,
        )
        db = self._make_omni_db(tmp_path, "test-secret-xyz")
        conns = load_omniroute_connections(db, secret="test-secret-xyz")
        nodes = load_omniroute_nodes(db)
        plan = plan_import(conns, nodes, existing_keys={"sk-or-v1-1111"})
        skipped = [i for i in plan["items"] if i.get("skip")]
        assert len(skipped) == 1
        assert skipped[0]["id"] == "c-apikey-1"
        assert plan["would_skip_existing"] == 1

    def test_no_plaintext_in_output(self, tmp_path, capsys, monkeypatch):
        """Regression: decrypted secrets never appear in run_import stdout."""
        from modules.daemon.src.capabilities_9router_import_omniroute import (
            load_omniroute_connections,
            load_omniroute_nodes,
            run_import,
        )
        db = self._make_omni_db(tmp_path, "test-secret-xyz")
        conns = load_omniroute_connections(db, secret="test-secret-xyz")
        nodes = load_omniroute_nodes(db)
        monkeypatch.setattr(
            "modules.daemon.src.capabilities_9router_import_omniroute.load_omniroute_connections",
            lambda *a, **kw: conns,
        )
        monkeypatch.setattr(
            "modules.daemon.src.capabilities_9router_import_omniroute.load_omniroute_nodes",
            lambda *a, **kw: nodes,
        )
        run_import(["--dry-run"])
        out = capsys.readouterr().out
        assert "sk-or-v1-1111" not in out
        assert "ya29.access" not in out
        assert "ya29.refresh" not in out
        assert "ya29.id" not in out
        assert "test-secret-xyz" not in out
        assert "(no writes performed)" in out

    def test_write_via_sqlite_dry_run_counts(self, tmp_path):
        from modules.daemon.src.capabilities_9router_import_omniroute import (
            load_omniroute_connections,
            load_omniroute_nodes,
            plan_import,
            write_via_sqlite,
        )
        db = self._make_omni_db(tmp_path, "test-secret-xyz")
        nine_db = tmp_path / "nine.sqlite"
        conn = sqlite3.connect(nine_db)
        conn.execute(
            "CREATE TABLE providerConnections(id TEXT PRIMARY KEY, provider TEXT, authType TEXT, "
            "name TEXT, email TEXT, priority INTEGER, isActive INTEGER, data TEXT NOT NULL, "
            "createdAt TEXT, updatedAt TEXT)"
        )
        conn.commit()
        conn.close()
        conns = load_omniroute_connections(db, secret="test-secret-xyz")
        nodes = load_omniroute_nodes(db)
        plan = plan_import(conns, nodes)
        counts = write_via_sqlite(plan["items"], db_path=str(nine_db), dry_run=True)
        assert counts["imported"] == plan["would_import"]
        assert counts["errors"] == 0

