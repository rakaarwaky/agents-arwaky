"""Unit tests for modules/harness — test individual functions and methods."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

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
        from modules.shared.src.contract_harness_protocol import IHarnessConnectProtocol

        connector = HarnessConnector({})
        assert isinstance(connector, IHarnessConnectProtocol)
        assert callable(getattr(connector, 'connect'))

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
        from modules.harness.src.capabilities_harness_disconnector import HarnessDisconnector

        disconnector = HarnessDisconnector({})
        assert disconnector is not None

    def test_disconnect_method_exists(self):
        """UT-HARNESS-006: the disconnect seam declares the named method."""
        from modules.harness.src.capabilities_harness_disconnector import HarnessDisconnector
        from modules.shared.src.contract_harness_protocol import IHarnessDisconnectProtocol

        disconnector = HarnessDisconnector({})
        assert isinstance(disconnector, IHarnessDisconnectProtocol)
        assert callable(getattr(disconnector, 'disconnect'))


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
        from modules.shared.src.contract_harness_protocol import IHarnessSkillsProtocol

        skills = HarnessSkills({})
        assert isinstance(skills, IHarnessSkillsProtocol)
        assert callable(getattr(skills, 'provision_skills'))


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
        from modules.shared.src.taxonomy_harness_vo import UnsupportedHarnessError

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
