"""Unit tests for modules/harness — test individual functions and methods."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


class TestHarnessConnector:
    """Tests for HarnessConnector class."""

    def test_init_creates_connector(self):
        """UT-HARNESS-001: HarnessConnector initializes correctly."""
        from modules.harness.src.capabilities_harness_connector import HarnessConnector

        connector = HarnessConnector({})
        assert connector is not None

    def test_init_with_adapters(self):
        """UT-HARNESS-002: HarnessConnector accepts adapters dict."""
        from modules.harness.src.capabilities_harness_connector import HarnessConnector

        adapters = {"test": MagicMock()}
        connector = HarnessConnector(adapters)
        assert connector._adapters == adapters

    def test_init_with_daemon_status_fn(self):
        """UT-HARNESS-003: HarnessConnector accepts daemon_status_fn."""
        from modules.harness.src.capabilities_harness_connector import HarnessConnector

        def status_fn():
            return True

        connector = HarnessConnector({}, daemon_status_fn=status_fn)
        assert connector._daemon_status_fn == status_fn

    def test_connect_method_exists(self):
        """UT-HARNESS-004: the connect seam declares the named method."""
        from modules.harness.src.capabilities_harness_connector import HarnessConnector
        from modules.shared.src.harness.contract_harness_protocol import (
            IHarnessConnectProtocol,
        )

        connector = HarnessConnector({})
        assert isinstance(connector, IHarnessConnectProtocol)
        assert callable(connector.connect)

    def test_provision_clause_delegates_to_injected_skills(self):
        """UT-HARNESS-004b: connect provisions skills via the injected seam."""
        from unittest.mock import MagicMock

        from modules.harness.src.capabilities_harness_connector import HarnessConnector

        skills = MagicMock()
        skills.provision_skills.return_value = 0
        connector = HarnessConnector({}, skills=skills)
        assert connector._skills is skills


class TestHarnessDisconnector:
    """Tests for HarnessDisconnector class."""

    def test_init_creates_disconnector(self):
        """UT-HARNESS-006: HarnessDisconnector initializes correctly."""
        from modules.harness.src.capabilities_harness_disconnector import (
            HarnessDisconnector,
        )

        disconnector = HarnessDisconnector({})
        assert disconnector is not None

    def test_disconnect_method_exists(self):
        """UT-HARNESS-006: the disconnect seam declares the named method."""
        from modules.harness.src.capabilities_harness_disconnector import (
            HarnessDisconnector,
        )
        from modules.shared.src.harness.contract_harness_protocol import (
            IHarnessDisconnectProtocol,
        )

        disconnector = HarnessDisconnector({})
        assert isinstance(disconnector, IHarnessDisconnectProtocol)
        assert callable(disconnector.disconnect)


class TestHarnessSkills:
    """Tests for HarnessSkills class."""

    def test_init_creates_skills(self):
        """UT-HARNESS-008: HarnessSkills initializes correctly."""
        from modules.harness.src.capabilities_harness_skills import HarnessSkills

        skills = HarnessSkills({})
        assert skills is not None

    def test_provision_skills_method_exists(self):
        """UT-HARNESS-008: the skills seam declares the named method."""
        from modules.harness.src.capabilities_harness_skills import HarnessSkills
        from modules.shared.src.harness.contract_harness_protocol import (
            IHarnessSkillsProtocol,
        )

        skills = HarnessSkills({})
        assert isinstance(skills, IHarnessSkillsProtocol)
        assert callable(skills.provision_skills)


class TestHarnessLeafAdapters:
    """Tests for the provider leaf protocol implementations (AES403)."""

    def test_execute_supported_for_own_id(self):
        """UT-HARNESS-010: a leaf reports participation for its own id."""
        from modules.harness.src.capabilities_harness_grok_build_adapter import (
            GrokBuildHarnessAdapter,
        )

        adapter = GrokBuildHarnessAdapter()
        assert adapter.execute("supported", ("grok-build",), {}) == 0

    def test_execute_rejects_op_outside_leaf_set(self):
        """UT-HARNESS-011: an op outside LEAF_OPS is a contract breach."""
        from modules.harness.src.capabilities_harness_grok_build_adapter import (
            GrokBuildHarnessAdapter,
        )

        adapter = GrokBuildHarnessAdapter()
        with pytest.raises(ValueError):
            adapter.execute("connect", ("grok-build",), {})

    def test_execute_unknown_harness_id_raises(self):
        """UT-HARNESS-012: an unregistered id raises the typed harness error."""
        from modules.harness.src.capabilities_harness_hermes_adapter import (
            HermesHarnessAdapter,
        )
        from modules.shared.src.harness.taxonomy_harness_vo import (
            UnsupportedHarnessError,
        )

        adapter = HermesHarnessAdapter()
        with pytest.raises(UnsupportedHarnessError):
            adapter.execute("supported", ("not-a-harness",), {})

    def test_execute_supported_respects_scope_flags(self):
        """UT-HARNESS-013: a scoped run needs that surface on the provider."""
        from types import SimpleNamespace

        from modules.harness.src.capabilities_harness_opencode_adapter import (
            OpencodeHarnessAdapter,
        )

        provider = SimpleNamespace(id="fake", supports_mcp=False, supports_env=True)
        adapter = OpencodeHarnessAdapter(units={"fake": provider})

        assert adapter.execute("supported", ("fake",), {}) == 0
        assert adapter.execute("supported", ("fake",), {"mcp_only": True}) == 1
        assert adapter.execute("supported", ("fake",), {"env_only": True}) == 0

    def test_execute_satisfied_tracks_provider_surface(self, tmp_path):
        """UT-HARNESS-014: satisfied follows the provider's declared files."""
        from types import SimpleNamespace

        from modules.harness.src.capabilities_harness_hermes_adapter import (
            HermesHarnessAdapter,
        )

        config_file = tmp_path / "config.yaml"
        env_file = tmp_path / ".env"
        provider = SimpleNamespace(
            id="fake",
            supports_mcp=True,
            supports_env=True,
            mcp_targets=lambda: (("Fake", tmp_path),),
            mcp_config_file=lambda target_dir: config_file,
            env_files=lambda: (env_file,),
        )
        adapter = HermesHarnessAdapter(units={"fake": provider})

        assert adapter.execute("satisfied", ("fake",), {}) == 1
        config_file.write_text("", encoding="utf-8")
        env_file.write_text("", encoding="utf-8")
        assert adapter.execute("satisfied", ("fake",), {}) == 0


# ---------------------------------------------------------------------------
# Dual-gateway (OmniRoute primary + 9router secondary) wiring
# ---------------------------------------------------------------------------
def _isolate_harness_home(tmp_path, monkeypatch):
    """Redirect every harness/XDG home into ``tmp_path`` for a stateless run."""
    from pathlib import Path

    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(Path, "home", classmethod(lambda _cls: home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg-data"))
    grok_home = tmp_path / "grok-home"
    grok_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("GROK_HOME", str(grok_home))
    monkeypatch.delenv("MAIN_COMBO", raising=False)
    monkeypatch.delenv("NINEROUTER_PORT", raising=False)
    return grok_home


def _write_cred_files(tmp_path, nine_key: str = "nine-key-abc"):
    """Write a valid OmniRoute env file and a 9router sibling env file."""
    omni = tmp_path / "omniroute.env"
    omni.write_text(
        'OMNIROUTE_URL="http://127.0.0.1:7777"\n'
        'OMNIROUTE_KEY="omni-key-xyz"\n',
        encoding="utf-8",
    )
    nine = tmp_path / "ninerouter.env"
    nine.write_text(
        'NINEROUTER_URL="http://127.0.0.1:20128"\n'
        f'NINEROUTER_KEY="{nine_key}"\n',
        encoding="utf-8",
    )
    return omni, nine


def _env_vars(path):
    """Parse ``KEY=value`` lines (quotes stripped) out of a .env-style file."""
    out = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            out[key] = value.strip().strip('"')
    return out


class TestDualGatewayAdapterSurface:
    """Adapters declare the symmetric dual-gateway surface."""

    def test_adapters_declare_symmetric_gateway_fields(self):
        """UT-HARNESS-018: env keys, candidates, confs, and router2 fields."""
        from modules.harness.src.root_harness_container import HARNESS_REGISTRY

        for harness_id in ("grok-build", "opencode", "hermes"):
            adapter = HARNESS_REGISTRY[harness_id]
            assert adapter.env_keys[:2] == ("OMNIROUTE_URL", "OMNIROUTE_KEY")
            assert adapter.env_keys[2:4] == ("NINEROUTER_URL", "NINEROUTER_KEY")
            assert "MNEMOSYNE_DATA_DIR" in adapter.env_keys
            confs = [conf.name for conf in adapter.session_conf_files()]
            assert confs == ["omniroute.conf", "9router.conf"]
            cands = [str(cand) for cand in adapter.credential_candidates()]
            assert cands[0].endswith("config/omniroute.env")
            assert any(cand.endswith("config/ninerouter.env") for cand in cands)
            assert any(cand.endswith(".9router/.env") for cand in cands)
            assert any(cand.endswith("9router/ninerouter.env") for cand in cands)

        # File-binding adapters carry the secondary router fields, primary
        # trio untouched.
        for harness_id in ("grok-build", "opencode"):
            adapter = HARNESS_REGISTRY[harness_id]
            assert adapter.router_provider_id == "myomniroute"
            assert adapter.router_provider_name == "omniroute"
            assert adapter.env_key == "OMNIROUTE_KEY"
            assert adapter.router2_provider_id == "my9router"
            assert adapter.router2_provider_name == "9router"
            assert adapter.router2_env_key == "NINEROUTER_KEY"

        # Hermes is env-only: no config-file binding, so no router2 fields.
        hermes = HARNESS_REGISTRY["hermes"]
        assert hermes.custom_api_kind == "router-env"
        assert not hasattr(hermes, "router2_provider_id")

    def test_get_9router_credentials_parses_and_defaults(self, tmp_path, monkeypatch):
        """UT-HARNESS-019: NINEROUTER parse mirrors the OMNIROUTE one."""
        from modules.harness.src.capabilities_harness_connector import (
            _get_9router_credentials,
        )

        monkeypatch.setenv("NINEROUTER_PORT", "30333")
        missing = tmp_path / "absent.env"
        assert _get_9router_credentials((missing,)).url == "http://127.0.0.1:30333"

        _omni, nine = _write_cred_files(tmp_path)
        creds = _get_9router_credentials((missing, nine))
        assert creds.url == "http://127.0.0.1:20128"
        assert creds.key == "nine-key-abc"


class TestDualGatewayEnvInjection:
    """Env injection carries both gateway pairs without regressing omni-only."""

    def test_both_gateway_env_files_inject_all_four_vars(self, tmp_path, monkeypatch):
        """UT-HARNESS-015: both credential sets -> all 4 gateway vars land."""
        from modules.harness.src.root_harness_container import HARNESS_REGISTRY

        grok_home = _isolate_harness_home(tmp_path, monkeypatch)
        omni, nine = _write_cred_files(tmp_path)
        adapter = HARNESS_REGISTRY["grok-build"]
        monkeypatch.setattr(
            type(adapter),
            "credential_candidates",
            lambda _self, candidates=(omni, nine): candidates,
        )
        conf_dir = tmp_path / "xdg-config" / "environment.d"
        conf_dir.mkdir(parents=True)
        omni_conf = conf_dir / "omniroute.conf"
        omni_conf.write_text(
            'OMNIROUTE_URL="http://127.0.0.1:7778"\nOMNIROUTE_KEY="stale"\n',
            encoding="utf-8",
        )

        from modules.harness.src.capabilities_harness_connector import HarnessConnector

        connector = HarnessConnector(HARNESS_REGISTRY)
        assert connector.connect(("grok-build",), env_only=True) == 0

        env = _env_vars(grok_home / ".env")
        for var in ("OMNIROUTE_URL", "OMNIROUTE_KEY", "NINEROUTER_URL", "NINEROUTER_KEY"):
            assert var in env, f"{var} missing from {grok_home / '.env'}"
        assert env["OMNIROUTE_KEY"] == "omni-key-xyz"
        assert env["NINEROUTER_KEY"] == "nine-key-abc"
        assert "MNEMOSYNE_DATA_DIR" in env

        # Each environment.d layer keeps only its own gateway's pair.
        omni_sync = _env_vars(omni_conf)
        assert omni_sync["OMNIROUTE_KEY"] == "omni-key-xyz"
        assert "NINEROUTER_KEY" not in omni_sync
        nine_sync = _env_vars(conf_dir / "9router.conf")
        assert nine_sync.get("NINEROUTER_KEY") == "nine-key-abc"
        assert "OMNIROUTE_KEY" not in nine_sync

    def test_omni_only_env_keeps_single_pair_and_warns(self, tmp_path, monkeypatch, capsys):
        """UT-HARNESS-016: without ninerouter.env today's omni-only run holds."""
        from modules.harness.src.root_harness_container import HARNESS_REGISTRY

        grok_home = _isolate_harness_home(tmp_path, monkeypatch)
        omni, _nine = _write_cred_files(tmp_path)
        adapter = HARNESS_REGISTRY["grok-build"]
        monkeypatch.setattr(
            type(adapter),
            "credential_candidates",
            lambda _self, candidates=(omni,): candidates,
        )
        conf_dir = tmp_path / "xdg-config" / "environment.d"
        conf_dir.mkdir(parents=True)
        omni_conf = conf_dir / "omniroute.conf"
        omni_conf.write_text('OMNIROUTE_URL="http://127.0.0.1:7778"\n', encoding="utf-8")

        from modules.harness.src.capabilities_harness_connector import HarnessConnector

        connector = HarnessConnector(HARNESS_REGISTRY)
        assert connector.connect(("grok-build",), env_only=True) == 0

        env = _env_vars(grok_home / ".env")
        assert env["OMNIROUTE_KEY"] == "omni-key-xyz"
        assert "MNEMOSYNE_DATA_DIR" in env
        assert "NINEROUTER_URL" not in env and "NINEROUTER_KEY" not in env

        # No 9router session layer without a real key; omni layer unchanged
        # in shape (its own pair only).
        assert not (conf_dir / "9router.conf").exists()
        omni_sync = _env_vars(omni_conf)
        assert omni_sync["OMNIROUTE_KEY"] == "omni-key-xyz"
        assert "NINEROUTER_KEY" not in omni_sync

        captured = capsys.readouterr()
        assert "No active 9Router API Key found" in captured.err
        assert "aa 9router" in captured.err
        assert (
            "Injected OMNIROUTE_URL/KEY + MNEMOSYNE_DATA_DIR into "
            "grok-build environment." in captured.out
        )

    def test_placeholder_9router_key_never_injected(self, tmp_path, monkeypatch, capsys):
        """UT-HARNESS-017: a placeholder 9router key degrades to omni-only."""
        from modules.harness.src.root_harness_container import HARNESS_REGISTRY

        grok_home = _isolate_harness_home(tmp_path, monkeypatch)
        omni, nine = _write_cred_files(
            tmp_path, nine_key="sk-your-9router-consumer-key-here"
        )
        adapter = HARNESS_REGISTRY["grok-build"]
        monkeypatch.setattr(
            type(adapter),
            "credential_candidates",
            lambda _self, candidates=(omni, nine): candidates,
        )
        conf_dir = tmp_path / "xdg-config" / "environment.d"
        conf_dir.mkdir(parents=True)

        from modules.harness.src.capabilities_harness_connector import HarnessConnector

        connector = HarnessConnector(HARNESS_REGISTRY)
        assert connector.connect(("grok-build",), env_only=True) == 0

        env_text = (grok_home / ".env").read_text(encoding="utf-8")
        assert "OMNIROUTE_KEY=" in env_text
        assert "NINEROUTER_KEY=" not in env_text
        assert "sk-your-9router-consumer-key-here" not in env_text
        assert not (conf_dir / "9router.conf").exists()
        assert "No active 9Router API Key found" in capsys.readouterr().err


class TestDualGatewayRouterBinding:
    """Config-file binding writes both providers and keeps omni behavior."""

    def test_config_toml_writes_both_provider_sections(self, tmp_path, monkeypatch):
        """UT-HARNESS-020: both TOML sections coexist; foreign model survives."""
        from modules.harness.src import (
            capabilities_harness_connector as connector_module,
        )
        from modules.harness.src.root_harness_container import HARNESS_REGISTRY
        from modules.shared.src.common.utility_config_engine import load_file

        grok_home = _isolate_harness_home(tmp_path, monkeypatch)
        omni, nine = _write_cred_files(tmp_path)
        adapter = HARNESS_REGISTRY["grok-build"]
        monkeypatch.setattr(
            type(adapter),
            "credential_candidates",
            lambda _self, candidates=(omni, nine): candidates,
        )
        cfg_file = grok_home / "config.toml"
        cfg_file.write_text(
            '[model.user-model]\nmodel = "gpt-user"\nname = "GPT User"\n'
            'model_provider = "userprov"\ncontext_window = 987\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(connector_module, "_probe_router", lambda *a, **k: 0)

        connector = connector_module.HarnessConnector(HARNESS_REGISTRY)
        assert connector.connect(("grok-build",), env_only=True, router=True) == 0

        data, _fmt = load_file(cfg_file)
        providers = data["model_providers"]
        assert providers["omniroute"] == {
            "base_url": "http://127.0.0.1:7777/v1",
            "api_backend": "chat_completions",
            "env_key": "OMNIROUTE_KEY",
        }
        assert providers["9router"] == {
            "base_url": "http://127.0.0.1:20128/v1",
            "api_backend": "chat_completions",
            "env_key": "NINEROUTER_KEY",
        }
        model = data["model"]
        assert model["myomniroute"]["model_provider"] == "omniroute"
        assert model["my9router"]["model_provider"] == "9router"
        assert model["user-model"]["model_provider"] == "userprov"
        assert model["user-model"]["context_window"] == 987
        assert data["models"]["default"] == "myomniroute"

    def test_config_toml_omni_only_writes_single_section(
        self, tmp_path, monkeypatch, capsys
    ):
        """UT-HARNESS-021: regression guard — omni-only creds, omni section only."""
        from modules.harness.src import (
            capabilities_harness_connector as connector_module,
        )
        from modules.harness.src.root_harness_container import HARNESS_REGISTRY
        from modules.shared.src.common.utility_config_engine import load_file

        grok_home = _isolate_harness_home(tmp_path, monkeypatch)
        omni, _nine = _write_cred_files(tmp_path)
        adapter = HARNESS_REGISTRY["grok-build"]
        monkeypatch.setattr(
            type(adapter),
            "credential_candidates",
            lambda _self, candidates=(omni,): candidates,
        )
        cfg_file = grok_home / "config.toml"
        cfg_file.write_text("", encoding="utf-8")
        monkeypatch.setattr(connector_module, "_probe_router", lambda *a, **k: 0)

        connector = connector_module.HarnessConnector(HARNESS_REGISTRY)
        assert connector.connect(("grok-build",), env_only=True, router=True) == 0

        data, _fmt = load_file(cfg_file)
        providers = data["model_providers"]
        assert "omniroute" in providers
        assert "9router" not in providers
        model = data["model"]
        assert "myomniroute" in model
        assert "my9router" not in model
        assert data["models"]["default"] == "myomniroute"
        captured = capsys.readouterr()
        assert "secondary gateway wiring SKIPPED" in captured.out
        assert "No active 9Router API Key found" in captured.err

    def test_opencode_json_writes_both_provider_objects(self, tmp_path, monkeypatch):
        """UT-HARNESS-022: both provider objects; primary selection untouched."""
        import json

        from modules.harness.src import (
            capabilities_harness_connector as connector_module,
        )
        from modules.harness.src.root_harness_container import HARNESS_REGISTRY

        _isolate_harness_home(tmp_path, monkeypatch)
        omni, nine = _write_cred_files(tmp_path)
        adapter = HARNESS_REGISTRY["opencode"]
        monkeypatch.setattr(
            type(adapter),
            "credential_candidates",
            lambda _self, candidates=(omni, nine): candidates,
        )
        cfg_dir = tmp_path / "xdg-config" / "opencode"
        cfg_dir.mkdir(parents=True)
        cfg_file = cfg_dir / "opencode.jsonc"
        cfg_file.write_text("{}\n", encoding="utf-8")
        monkeypatch.setattr(connector_module, "_probe_router", lambda *a, **k: 0)

        connector = connector_module.HarnessConnector(HARNESS_REGISTRY)
        assert connector.connect(("opencode",), env_only=True, router=True) == 0

        settings = json.loads(cfg_file.read_text(encoding="utf-8"))
        providers = settings["provider"]
        assert {"omniroute", "9router"} <= set(providers)
        assert providers["omniroute"]["options"]["baseURL"] == "http://127.0.0.1:7777/v1"
        assert providers["omniroute"]["options"]["apiKey"] == "omni-key-xyz"
        assert providers["omniroute"]["name"] == "OmniRoute (local)"
        assert providers["9router"]["options"]["baseURL"] == "http://127.0.0.1:20128/v1"
        assert providers["9router"]["options"]["apiKey"] == "nine-key-abc"
        assert providers["9router"]["name"] == "9Router (local, offline)"
        assert "my9router" in providers["9router"]["models"]
        assert settings["model"] == "omniroute/myomniroute"

    def test_settings_jsonc_drops_rotated_qwen_shadow_key(self, tmp_path, monkeypatch):
        """UT-HARNESS-023: the omni dedupe block still drops the inline shadow."""
        import json
        from types import SimpleNamespace

        from modules.harness.src import (
            capabilities_harness_connector as connector_module,
        )

        settings_file = tmp_path / "settings.json"
        settings_file.write_text(
            json.dumps(
                {
                    "modelProviders": {
                        "openai": [
                            {
                                "id": "myomniroute",
                                "name": "myomniroute",
                                "baseUrl": "http://127.0.0.1:7777/v1",
                                "envKey": "QWEN_CUSTOM_API_KEY_MODEL",
                            }
                        ]
                    },
                    "env": {"QWEN_CUSTOM_API_KEY_MODEL": "inline-stale-key"},
                    "security": {"auth": {"selectedType": "custom"}},
                    "model": {"name": "myomniroute"},
                }
            ),
            encoding="utf-8",
        )
        adapter = SimpleNamespace(
            id="qwen-proxy",
            mcp_config_file=lambda: settings_file,
            router_provider_id="myomniroute",
            env_key="OMNIROUTE_KEY",
        )
        monkeypatch.setattr(connector_module, "_probe_router", lambda *a, **k: 0)

        opts = connector_module.ConnectOpts()
        assert (
            connector_module._connect_router_settings(
                adapter, "http://127.0.0.1:7777", "omni-key-xyz", opts
            )
            == 0
        )

        settings = json.loads(settings_file.read_text(encoding="utf-8"))
        entry = settings["modelProviders"]["openai"][0]
        assert entry["envKey"] == "OMNIROUTE_KEY"
        assert "QWEN_CUSTOM_API_KEY_MODEL" not in settings.get("env", {})
        assert settings["security"]["auth"]["selectedType"] == "openai"
