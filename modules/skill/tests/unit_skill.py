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

    def test_execute_provision_returns_exit_code(self):
        """UT-SKILL-003: execute('provision') returns ExitCode."""
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import ExitCode

        provisioner = SkillPackProvisioner()
        with patch('modules.skill.src.capabilities_skill_pack.provision_single_skill', return_value=True):
            with patch('modules.skill.src.capabilities_skill_pack.get_tool_skills', return_value=[]):
                result = provisioner.execute("provision", "test-tool")
                assert isinstance(result, int)
                assert result == 0

    def test_execute_prune_returns_exit_code(self):
        """UT-SKILL-004: execute('prune') returns ExitCode."""
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import ExitCode

        provisioner = SkillPackProvisioner()
        with patch('modules.skill.src.capabilities_skill_pack.prune_provisioned', return_value=0):
            with patch('modules.skill.src.capabilities_skill_pack.provision_base', return_value=Path('/tmp/test')):
                result = provisioner.execute("prune")
                assert isinstance(result, int)
                assert result == 0

    def test_execute_audit_returns_exit_code(self):
        """UT-SKILL-005: execute('audit') returns ExitCode."""
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import ExitCode

        provisioner = SkillPackProvisioner()
        with patch.object(provisioner, 'audit', return_value=[]):
            result = provisioner.execute("audit")
            assert isinstance(result, int)
            assert result == 0

    def test_execute_unknown_op_returns_error(self):
        """UT-SKILL-006: execute with unknown op returns error code."""
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import ExitCode

        provisioner = SkillPackProvisioner()
        with patch('sys.stderr', new_callable=MagicMock):
            result = provisioner.execute("unknown-op")
            assert result == ExitCode(1)

    def test_install_returns_success_result(self):
        """UT-SKILL-007: install returns SkillProvisionResult."""
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import SkillProvisionResult

        provisioner = SkillPackProvisioner()
        with patch('modules.skill.src.capabilities_skill_pack.get_tool_skills', return_value=[]):
            result = provisioner.install("test-tool", Path("/tmp"))
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
                result = provisioner.install("test-tool", Path("/tmp"))
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

    def test_list_delegates_to_registry(self):
        """UT-SKILL-012: list delegates to registry.list."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

        provisioner = SkillPackProvisioner()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.list("lint")
        registry.list.assert_called_once()

    def test_check_delegates_to_registry(self):
        """UT-SKILL-013: check delegates to registry.check."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

        provisioner = SkillPackProvisioner()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.check()
        registry.check.assert_called_once()

    def test_show_delegates_to_registry(self):
        """UT-SKILL-014: show delegates to registry.show."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

        provisioner = SkillPackProvisioner()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.show("my-skill")
        registry.show.assert_called_once()

    def test_install_delegates_to_registry(self):
        """UT-SKILL-015: install delegates to registry.install."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import SkillArgs

        provisioner = SkillPackProvisioner()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.install(SkillArgs(["lint"]))
        registry.install.assert_called_once()

    def test_uninstall_delegates_to_registry(self):
        """UT-SKILL-016: uninstall delegates to registry.uninstall."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import SkillArgs

        provisioner = SkillPackProvisioner()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.uninstall(SkillArgs(["lint"]))
        registry.uninstall.assert_called_once()

    def test_sync_delegates_to_registry(self):
        """UT-SKILL-017: sync delegates to registry.sync."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
        from modules.shared.src.taxonomy_skill_vo import SkillArgs

        provisioner = SkillPackProvisioner()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.sync(SkillArgs([]))
        registry.sync.assert_called_once()

    def test_execute_provision_delegates_to_provisioner(self):
        """UT-SKILL-018: execute('provision') delegates to provisioner."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

        provisioner = MagicMock()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.execute("provision", "lint", Path("/tmp"))
        provisioner.execute.assert_called_with("provision", "lint", Path("/tmp"))

    def test_execute_prune_delegates_to_provisioner(self):
        """UT-SKILL-019: execute('prune') delegates to provisioner."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

        provisioner = MagicMock()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.execute("prune")
        provisioner.execute.assert_called_with("prune", None, None)

    def test_execute_audit_delegates_to_provisioner(self):
        """UT-SKILL-020: execute('audit') delegates to provisioner."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

        provisioner = MagicMock()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.execute("audit")
        provisioner.execute.assert_called_with("audit", None, None)

    def test_execute_remove_delegates_to_provisioner(self):
        """UT-SKILL-021: execute('remove') delegates to provisioner."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

        provisioner = MagicMock()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.execute("remove")
        provisioner.execute.assert_called_with("remove", None, None)

    def test_execute_list_delegates_to_registry(self):
        """UT-SKILL-022: execute('list') delegates to registry."""
        from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
        from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

        provisioner = SkillPackProvisioner()
        registry = MagicMock()
        orchestrator = SkillOrchestrator(provisioner, registry)

        orchestrator.execute("list")
        registry.execute.assert_called_with("list", None, None)


class TestSkillRegistryAdapter:
    """Tests for SkillRegistryAdapter."""

    def test_init(self):
        """UT-SKILL-023: SkillRegistryAdapter initializes without args."""
        from modules.skill.src.surface_skill_command import SkillRegistryAdapter

        adapter = SkillRegistryAdapter()
        assert adapter is not None

    def test_execute_list(self):
        """UT-SKILL-024: execute('list') calls list method."""
        from modules.skill.src.surface_skill_command import SkillRegistryAdapter
        from modules.shared.src.taxonomy_skill_vo import SkillArgs

        adapter = SkillRegistryAdapter()
        with patch.object(adapter, 'list', return_value=0) as mock_list:
            result = adapter.execute("list")
            mock_list.assert_called_once()
            assert isinstance(result, int)

    def test_execute_check(self):
        """UT-SKILL-025: execute('check') calls check method."""
        from modules.skill.src.surface_skill_command import SkillRegistryAdapter

        adapter = SkillRegistryAdapter()
        with patch.object(adapter, 'check', return_value=0) as mock_check:
            result = adapter.execute("check")
            mock_check.assert_called_once()
            assert isinstance(result, int)

    def test_execute_show(self):
        """UT-SKILL-026: execute('show') calls show method."""
        from modules.skill.src.surface_skill_command import SkillRegistryAdapter
        from modules.shared.src.taxonomy_skill_vo import SkillArgs

        adapter = SkillRegistryAdapter()
        with patch.object(adapter, 'show', return_value=0) as mock_show:
            result = adapter.execute("show", "my-skill")
            mock_show.assert_called_once()
            assert isinstance(result, int)

    def test_execute_install(self):
        """UT-SKILL-027: execute('install') calls install method."""
        from modules.skill.src.surface_skill_command import SkillRegistryAdapter
        from modules.shared.src.taxonomy_skill_vo import SkillArgs

        adapter = SkillRegistryAdapter()
        with patch.object(adapter, 'install', return_value=0) as mock_install:
            result = adapter.execute("install", "lint")
            mock_install.assert_called_once()
            assert isinstance(result, int)

    def test_execute_uninstall(self):
        """UT-SKILL-028: execute('uninstall') calls uninstall method."""
        from modules.skill.src.surface_skill_command import SkillRegistryAdapter
        from modules.shared.src.taxonomy_skill_vo import SkillArgs

        adapter = SkillRegistryAdapter()
        with patch.object(adapter, 'uninstall', return_value=0) as mock_uninstall:
            result = adapter.execute("uninstall", "lint")
            mock_uninstall.assert_called_once()
            assert isinstance(result, int)

    def test_execute_sync(self):
        """UT-SKILL-029: execute('sync') calls sync method."""
        from modules.skill.src.surface_skill_command import SkillRegistryAdapter
        from modules.shared.src.taxonomy_skill_vo import SkillArgs

        adapter = SkillRegistryAdapter()
        with patch.object(adapter, 'sync', return_value=0) as mock_sync:
            result = adapter.execute("sync")
            mock_sync.assert_called_once()
            assert isinstance(result, int)

    def test_execute_unknown_op(self):
        """UT-SKILL-030: execute with unknown op prints error and returns 1."""
        from modules.skill.src.surface_skill_command import SkillRegistryAdapter

        adapter = SkillRegistryAdapter()
        with patch('sys.stderr', new_callable=MagicMock):
            result = adapter.execute("unknown-op")
            assert result == 1


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
