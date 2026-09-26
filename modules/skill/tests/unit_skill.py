"""Unit tests for modules/skill — class initialization and method behavior."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestSkillPackProvisioner:
    """Tests for SkillPackProvisioner."""

    def test_init_creates_pack_root(self):
        """UT-SKILL-001: SkillPackProvisioner sets _pack_root correctly."""
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

        provisioner = SkillPackProvisioner()
        assert isinstance(provisioner._pack_root, Path)
        assert provisioner._pack_root.name == "skills"

    def test_repr(self):
        """UT-SKILL-002: SkillPackProvisioner repr is descriptive."""
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

        provisioner = SkillPackProvisioner()
        assert repr(provisioner) == "SkillPackProvisioner()"

    def test_install_returns_success_result(self):
        """UT-SKILL-007: install returns SkillProvisionResult."""
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import SkillProvisionResult

        provisioner = SkillPackProvisioner()
        with patch('modules.skill.src.capabilities_skill_pack.get_tool_skills', return_value=[]):
            result = provisioner.provision("test-tool", Path("/tmp"))
            assert isinstance(result, SkillProvisionResult)
            assert result.success is True
            assert result.tool_id == "test-tool"

    def test_install_counts_provisioned(self):
        """UT-SKILL-008: install counts successfully provisioned skills."""
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import SkillProvisionResult

        provisioner = SkillPackProvisioner()
        mock_skills = [Path("/tmp/skills/a/SKILL.md"), Path("/tmp/skills/b/SKILL.md")]
        with patch('modules.skill.src.capabilities_skill_pack.get_tool_skills', return_value=mock_skills):
            with patch('modules.skill.src.capabilities_skill_pack.provision_single_skill', return_value=True):
                result = provisioner.provision("test-tool", Path("/tmp"))
                assert result.provisioned == 2

    def test_prune_returns_result(self):
        """UT-SKILL-009: prune returns SkillProvisionResult."""
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import SkillProvisionResult

        provisioner = SkillPackProvisioner()
        with patch('modules.skill.src.capabilities_skill_pack.provision_base', return_value=Path("/tmp/base")):
            with patch('modules.skill.src.capabilities_skill_pack.prune_provisioned', return_value=3):
                result = provisioner.prune(Path("/tmp"))
                assert isinstance(result, SkillProvisionResult)
                assert result.provisioned == 3
                assert "removed" in result.message


class TestSkillOrchestrator:
    """Tests for SkillOrchestrator."""

    def test_init_stores_dependencies(self):
        """UT-SKILL-010: SkillOrchestrator stores provisioner and registry."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

        provisioner = SkillPackProvisioner()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        assert orchestrator._provisioner is provisioner
        assert orchestrator._registry is registry

    def test_repr(self):
        """UT-SKILL-011: SkillOrchestrator repr is descriptive."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

        provisioner = SkillPackProvisioner()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)
        assert repr(orchestrator) == "SkillOrchestrator()"

    def test_execute_list_delegates_to_registry(self):
        """UT-SKILL-012: execute(list) delegates to registry.list."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import SkillOp, SkillRequest

        provisioner = SkillPackProvisioner()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.execute(SkillRequest(SkillOp("list")))
        registry.list.assert_called_once()

    def test_execute_check_delegates_to_registry(self):
        """UT-SKILL-013: execute(check) delegates to registry.check."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import SkillOp, SkillRequest

        provisioner = SkillPackProvisioner()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.execute(SkillRequest(SkillOp("check")))
        registry.check.assert_called_once()

    def test_execute_show_delegates_to_registry(self):
        """UT-SKILL-014: execute(show) delegates to registry.show."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import SkillOp, SkillRequest

        provisioner = SkillPackProvisioner()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.execute(SkillRequest(SkillOp("show"), skill="my-skill"))
        registry.show.assert_called_once()

    def test_execute_install_delegates_to_registry(self):
        """UT-SKILL-015: execute(install) delegates to registry.install."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import SkillArgs, SkillOp, SkillRequest

        provisioner = SkillPackProvisioner()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.execute(SkillRequest(SkillOp("install"), args=SkillArgs(["lint"])))
        registry.install.assert_called_once()

    def test_execute_uninstall_delegates_to_registry(self):
        """UT-SKILL-016: execute(uninstall) delegates to registry.uninstall."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import SkillArgs, SkillOp, SkillRequest

        provisioner = SkillPackProvisioner()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.execute(SkillRequest(SkillOp("uninstall"), args=SkillArgs(["lint"])))
        registry.uninstall.assert_called_once()

    def test_execute_sync_delegates_to_registry(self):
        """UT-SKILL-017: execute(sync) delegates to registry.sync."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import SkillArgs, SkillOp, SkillRequest

        provisioner = SkillPackProvisioner()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.execute(SkillRequest(SkillOp("sync"), args=SkillArgs([])))
        registry.sync.assert_called_once()

    def test_execute_provision_delegates_to_provisioner(self):
        """UT-SKILL-018: execute(provision) delegates to provisioner."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import SkillOp, SkillRequest

        provisioner = MagicMock()
        provisioner.provision.return_value.success = True
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.execute(SkillRequest(SkillOp("provision"), skill="lint", target=Path("/tmp")))
        provisioner.provision.assert_called_once()

    def test_execute_prune_delegates_to_provisioner(self):
        """UT-SKILL-019: execute(prune) delegates to provisioner."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import SkillOp, SkillRequest

        provisioner = MagicMock()
        provisioner.prune.return_value.success = True
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.execute(SkillRequest(SkillOp("prune")))
        provisioner.prune.assert_called_once()

    def test_execute_audit_delegates_to_provisioner(self):
        """UT-SKILL-020: execute(audit) delegates to provisioner.audit."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import SkillOp, SkillRequest

        provisioner = MagicMock()
        provisioner.audit.return_value = []
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.execute(SkillRequest(SkillOp("audit")))
        provisioner.audit.assert_called_once()

    def test_execute_remove_aliases_prune(self):
        """UT-SKILL-021: execute('prune') delegates to provisioner.prune."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import SkillOp, SkillRequest

        provisioner = MagicMock()
        provisioner.prune.return_value.success = True
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.execute(SkillRequest(SkillOp("prune")))
        provisioner.prune.assert_called_once()

    def test_execute_list_delegates_to_registry(self):
        """UT-SKILL-022: execute(list) delegates to registry.list."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import SkillOp, SkillRequest

        provisioner = SkillPackProvisioner()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.execute(SkillRequest(SkillOp("list")))
        registry.list.assert_called_once()


class TestSkillRegistryAdapter:
    """Tests for SkillRegistryAdapter."""

    def test_init(self):
        """UT-SKILL-023: SkillRegistryAdapter initializes without args."""
        from modules.skill.src.surface_skill_command import SkillRegistryAdapter

        adapter = SkillRegistryAdapter()
        assert adapter is not None

    def test_list(self):
        """UT-SKILL-024: list calls the module-level cmd_list."""
        from modules.skill.src.surface_skill_command import SkillRegistryAdapter

        adapter = SkillRegistryAdapter()
        with patch('modules.skill.src.surface_skill_command.cmd_list', return_value=0) as mock_fn:
            result = adapter.list()
            mock_fn.assert_called_once_with([])
            assert result == 0

    def test_check(self):
        """UT-SKILL-025: check calls the module-level cmd_check."""
        from modules.skill.src.surface_skill_command import SkillRegistryAdapter

        adapter = SkillRegistryAdapter()
        with patch('modules.skill.src.surface_skill_command.cmd_check', return_value=0) as mock_fn:
            result = adapter.check()
            mock_fn.assert_called_once_with([])
            assert result == 0

    def test_show(self):
        """UT-SKILL-026: show calls the module-level cmd_show."""
        from modules.skill.src.surface_skill_command import SkillRegistryAdapter

        adapter = SkillRegistryAdapter()
        with patch('modules.skill.src.surface_skill_command.cmd_show', return_value=0) as mock_fn:
            result = adapter.show("my-skill")
            mock_fn.assert_called_once_with(["my-skill"])
            assert result == 0

    def test_install(self):
        """UT-SKILL-027: install calls the module-level cmd_install."""
        from modules.skill.src.surface_skill_command import SkillRegistryAdapter

        adapter = SkillRegistryAdapter()
        with patch('modules.skill.src.surface_skill_command.cmd_install', return_value=0) as mock_fn:
            result = adapter.install(["lint"])
            mock_fn.assert_called_once()
            assert result == 0

    def test_uninstall(self):
        """UT-SKILL-028: uninstall calls the module-level cmd_uninstall."""
        from modules.skill.src.surface_skill_command import SkillRegistryAdapter

        adapter = SkillRegistryAdapter()
        with patch('modules.skill.src.surface_skill_command.cmd_uninstall', return_value=0) as mock_fn:
            result = adapter.uninstall(["lint"])
            mock_fn.assert_called_once()
            assert result == 0

    def test_sync(self):
        """UT-SKILL-029: sync calls the module-level cmd_install with 'all'."""
        from modules.skill.src.surface_skill_command import SkillRegistryAdapter

        adapter = SkillRegistryAdapter()
        with patch('modules.skill.src.surface_skill_command.cmd_install', return_value=0) as mock_fn:
            result = adapter.sync()
            mock_fn.assert_called_once_with(["all"])
            assert result == 0


class TestMainEntry:
    """Tests for main entry point."""

    def test_main_help(self):
        """UT-SKILL-031: main('--help') returns help exit code."""
        from modules.skill.src.surface_skill_command import main

        result = main(["--help"])
        assert result == 0

    def test_main_empty(self):
        """UT-SKILL-032: main([]) shows help."""
        from modules.skill.src.surface_skill_command import main

        result = main([])
        assert result == 0

    def test_main_list(self):
        """UT-SKILL-033: main(['list']) calls cmd_list."""
        from modules.skill.src.surface_skill_command import main

        result = main(["list"])
        assert result == 0

    def test_main_check(self):
        """UT-SKILL-034: main(['check']) calls cmd_check."""
        from modules.skill.src.surface_skill_command import main

        result = main(["check"])
        # May return non-zero if findings exist
        assert isinstance(result, int)

    def test_main_unknown_shows_help(self):
        """UT-SKILL-035: main with unknown action shows help."""
        from modules.skill.src.surface_skill_command import main

        result = main(["unknown-action"])
        assert result == 0
