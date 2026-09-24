"""Unit tests for modules/tools — capability classes and helper functions."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch


class TestInstallerCapability:
    """Tests for InstallerCapability."""

    def test_init_with_defaults(self):
        """UT-TOOLS-001: InstallerCapability initializes with defaults."""
        from modules.tools.src.capabilities_tools_installer import InstallerCapability

        installer = InstallerCapability()
        assert installer._root is None
        assert installer._daemons is None
        assert installer._facade is None

    def test_init_with_params(self):
        """UT-TOOLS-002: InstallerCapability initializes with explicit params."""
        from modules.tools.src.capabilities_tools_installer import InstallerCapability

        root = Path("/test/root")
        daemons = MagicMock()
        facade = MagicMock()
        installer = InstallerCapability(root=root, daemons=daemons, adapter_facade=facade)

        assert installer._root == root
        assert installer._daemons == daemons
        assert installer._facade == facade

    def test_execute_dispatches_install(self):
        """UT-TOOLS-003: execute dispatches 'install' op to install method."""
        from modules.tools.src.capabilities_tools_installer import InstallerCapability
        from modules.shared.src.taxonomy_common_vo import ToolSpec

        facade = MagicMock()
        installer = InstallerCapability(adapter_facade=facade)
        spec = ToolSpec(
            id="test-tool",
            category="dev",
            binary="test",
            is_mcp=False,
            description="test",
            path="/test",
            alias=None,
            mcp_binary=None,
            runner="",
        )

        result = installer.execute("install", spec=spec)
        assert result is not None

    def test_execute_rejects_wrong_op(self):
        """UT-TOOLS-004: execute raises on wrong op."""
        from modules.tools.src.capabilities_tools_installer import InstallerCapability
        from modules.shared.src.taxonomy_common_error import ToolInstallError
        from modules.shared.src.taxonomy_common_vo import ToolSpec

        installer = InstallerCapability()
        spec = ToolSpec(
            id="test-tool",
            category="dev",
            binary="test",
            is_mcp=False,
            description="test",
            path="/test",
            alias=None,
            mcp_binary=None,
            runner="",
        )

        try:
            installer.execute("wrong-op", spec=spec)
            assert False, "Should have raised ToolInstallError"
        except ToolInstallError:
            pass

    def test_execute_rejects_missing_spec(self):
        """UT-TOOLS-005: execute raises when spec is None."""
        from modules.tools.src.capabilities_tools_installer import InstallerCapability
        from modules.shared.src.taxonomy_common_error import ToolInstallError

        installer = InstallerCapability()

        try:
            installer.execute("install", spec=None)
            assert False, "Should have raised ToolInstallError"
        except ToolInstallError:
            pass

    def test_dry_run_returns_result(self):
        """UT-TOOLS-006: dry-run returns InstallResult without side effects."""
        from modules.tools.src.capabilities_tools_installer import InstallerCapability
        from modules.shared.src.taxonomy_common_vo import ToolSpec

        facade = MagicMock()
        installer = InstallerCapability(adapter_facade=facade)
        spec = ToolSpec(
            id="test-tool",
            category="dev",
            binary="test",
            is_mcp=False,
            description="test",
            path="/test",
            alias=None,
            mcp_binary=None,
            runner="",
        )

        result = installer.execute("install", spec=spec, args=["dry-run"])
        assert result.success is True
        assert "[dry-run]" in result.message

    def test_missing_facade_raises(self):
        """UT-TOOLS-007: missing facade raises ToolInstallError."""
        from modules.tools.src.capabilities_tools_installer import InstallerCapability
        from modules.shared.src.taxonomy_common_error import ToolInstallError
        from modules.shared.src.taxonomy_common_vo import ToolSpec

        installer = InstallerCapability()
        spec = ToolSpec(
            id="test-tool",
            category="dev",
            binary="test",
            is_mcp=False,
            description="test",
            path="/test",
            alias=None,
            mcp_binary=None,
            runner="",
        )

        try:
            installer.install(spec)
            assert False, "Should have raised ToolInstallError"
        except ToolInstallError as e:
            assert "adapter facade is not wired" in str(e)


class TestUpdaterCapability:
    """Tests for UpdaterCapability."""

    def test_init_with_defaults(self):
        """UT-TOOLS-008: UpdaterCapability initializes with defaults."""
        from modules.tools.src.capabilities_tools_updater import UpdaterCapability

        updater = UpdaterCapability()
        assert updater._root is None
        assert updater._facade is None

    def test_init_with_params(self):
        """UT-TOOLS-009: UpdaterCapability initializes with explicit params."""
        from modules.tools.src.capabilities_tools_updater import UpdaterCapability

        root = Path("/test/root")
        facade = MagicMock()
        updater = UpdaterCapability(root=root, adapter_facade=facade)

        assert updater._root == root
        assert updater._facade == facade

    def test_execute_dispatches_update(self):
        """UT-TOOLS-010: execute dispatches 'update' op to update method."""
        from modules.tools.src.capabilities_tools_updater import UpdaterCapability
        from modules.shared.src.taxonomy_common_vo import ToolSpec

        facade = MagicMock()
        facade.is_pin_satisfied.return_value = (False, "outdated")
        updater = UpdaterCapability(adapter_facade=facade)
        spec = ToolSpec(
            id="test-tool",
            category="dev",
            binary="test",
            is_mcp=False,
            description="test",
            path="/test",
            alias=None,
            mcp_binary=None,
            runner="",
        )

        result = updater.execute("update", spec=spec, query=facade)
        assert result is not None

    def test_execute_rejects_wrong_op(self):
        """UT-TOOLS-011: execute raises on wrong op."""
        from modules.tools.src.capabilities_tools_updater import UpdaterCapability
        from modules.shared.src.taxonomy_common_error import ToolUpdateError
        from modules.shared.src.taxonomy_common_vo import ToolSpec

        updater = UpdaterCapability()
        spec = ToolSpec(
            id="test-tool",
            category="dev",
            binary="test",
            is_mcp=False,
            description="test",
            path="/test",
            alias=None,
            mcp_binary=None,
            runner="",
        )

        try:
            updater.execute("wrong-op", spec=spec)
            assert False, "Should have raised ToolUpdateError"
        except ToolUpdateError:
            pass

    def test_dry_run_returns_result(self):
        """UT-TOOLS-012: dry-run returns UpdateResult without side effects."""
        from modules.tools.src.capabilities_tools_updater import UpdaterCapability
        from modules.shared.src.taxonomy_common_vo import ToolSpec

        facade = MagicMock()
        facade.is_pin_satisfied.return_value = (False, "outdated")
        updater = UpdaterCapability(adapter_facade=facade)
        spec = ToolSpec(
            id="test-tool",
            category="dev",
            binary="test",
            is_mcp=False,
            description="test",
            path="/test",
            alias=None,
            mcp_binary=None,
            runner="",
        )

        result = updater.execute("update", spec=spec, args=["dry-run"])
        assert result.success is True
        assert "[dry-run]" in result.message


class TestUninstallerCapability:
    """Tests for UninstallerCapability."""

    def test_init_with_defaults(self):
        """UT-TOOLS-013: UninstallerCapability initializes with defaults."""
        from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability

        uninstaller = UninstallerCapability()
        assert uninstaller._daemons is None

    def test_init_with_daemons(self):
        """UT-TOOLS-014: UninstallerCapability initializes with daemons."""
        from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability

        daemons = MagicMock()
        uninstaller = UninstallerCapability(daemons=daemons)
        assert uninstaller._daemons == daemons

    def test_execute_dispatches_uninstall(self):
        """UT-TOOLS-015: execute dispatches 'uninstall' op to uninstall method."""
        from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability
        from modules.shared.src.taxonomy_common_vo import ToolSpec

        uninstaller = UninstallerCapability()
        spec = ToolSpec(
            id="test-tool",
            category="dev",
            binary="test",
            is_mcp=False,
            description="test",
            path="/test",
            alias=None,
            mcp_binary=None,
            runner="",
        )

        result = uninstaller.execute("uninstall", spec=spec)
        assert result is not None

    def test_execute_rejects_wrong_op(self):
        """UT-TOOLS-016: execute raises on wrong op."""
        from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability
        from modules.shared.src.taxonomy_common_error import ToolUninstallError
        from modules.shared.src.taxonomy_common_vo import ToolSpec

        uninstaller = UninstallerCapability()
        spec = ToolSpec(
            id="test-tool",
            category="dev",
            binary="test",
            is_mcp=False,
            description="test",
            path="/test",
            alias=None,
            mcp_binary=None,
            runner="",
        )

        try:
            uninstaller.execute("wrong-op", spec=spec)
            assert False, "Should have raised ToolUninstallError"
        except ToolUninstallError:
            pass

    def test_dry_run_returns_result(self):
        """UT-TOOLS-017: dry-run returns UninstallResult without side effects."""
        from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability
        from modules.shared.src.taxonomy_common_vo import ToolSpec

        uninstaller = UninstallerCapability()
        spec = ToolSpec(
            id="test-tool",
            category="dev",
            binary="test",
            is_mcp=False,
            description="test",
            path="/test",
            alias=None,
            mcp_binary=None,
            runner="",
        )

        result = uninstaller.execute("uninstall", spec=spec, args=["dry-run"])
        assert result is not None


class TestRunnerCapability:
    """Tests for RunnerCapability."""

    def test_init_with_defaults(self):
        """UT-TOOLS-018: RunnerCapability initializes with defaults."""
        from modules.tools.src.capabilities_tools_runner import RunnerCapability

        runner = RunnerCapability()
        assert runner._root is None

    def test_init_with_root(self):
        """UT-TOOLS-019: RunnerCapability initializes with explicit root."""
        from modules.tools.src.capabilities_tools_runner import RunnerCapability

        root = Path("/test/root")
        runner = RunnerCapability(root=root)
        assert runner._root == root

    def test_execute_dispatches_run(self):
        """UT-TOOLS-020: execute dispatches 'run' op to run method."""
        from modules.tools.src.capabilities_tools_runner import RunnerCapability
        from modules.shared.src.taxonomy_common_vo import ToolSpec

        runner = RunnerCapability()
        spec = ToolSpec(
            id="test-tool",
            category="dev",
            binary="test",
            is_mcp=False,
            description="test",
            path="/test",
            alias=None,
            mcp_binary=None,
            runner="",
        )

        result = runner.execute("run", spec=spec, args=[])
        assert result is not None

    def test_execute_dispatches_discover(self):
        """UT-TOOLS-021: execute dispatches 'discover' op to discover method."""
        from modules.tools.src.capabilities_tools_runner import RunnerCapability
        from modules.shared.src.taxonomy_common_vo import ToolSpec

        runner = RunnerCapability()
        spec = ToolSpec(
            id="test-tool",
            category="dev",
            binary="test",
            is_mcp=False,
            description="test",
            path="/test",
            alias=None,
            mcp_binary=None,
            runner="",
        )

        result = runner.execute("discover", spec=spec)
        assert result is None or isinstance(result, Path)

    def test_execute_rejects_missing_spec(self):
        """UT-TOOLS-022: execute raises when spec is None."""
        from modules.tools.src.capabilities_tools_runner import RunnerCapability
        from modules.shared.src.taxonomy_common_error import ToolInstallError

        runner = RunnerCapability()

        try:
            runner.execute("run")
            assert False, "Should have raised ToolInstallError"
        except ToolInstallError:
            pass

    def test_execute_rejects_wrong_op(self):
        """UT-TOOLS-023: execute raises on wrong op."""
        from modules.tools.src.capabilities_tools_runner import RunnerCapability
        from modules.shared.src.taxonomy_common_error import ToolInstallError
        from modules.shared.src.taxonomy_common_vo import ToolSpec

        runner = RunnerCapability()
        spec = ToolSpec(
            id="test-tool",
            category="dev",
            binary="test",
            is_mcp=False,
            description="test",
            path="/test",
            alias=None,
            mcp_binary=None,
            runner="",
        )

        try:
            runner.execute("wrong-op", spec=spec)
            assert False, "Should have raised ToolInstallError"
        except ToolInstallError:
            pass


class TestVersionProbe:
    """Tests for _version_probe helper."""

    def test_version_probe_success(self):
        """UT-TOOLS-024: _version_probe returns version string on success."""
        from modules.tools.src.capabilities_tools_installer import _version_probe
        from unittest.mock import patch, MagicMock

        mock_proc = MagicMock()
        mock_proc.stdout = "test-tool 1.2.3\n"
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc) as mock_run:
            result = _version_probe("test-tool")
            assert result == "test-tool 1.2.3"
            mock_run.assert_called_once()

    def test_version_probe_missing_binary(self):
        """UT-TOOLS-025: _version_probe returns empty on missing binary."""
        from modules.tools.src.capabilities_tools_installer import _version_probe
        from unittest.mock import patch

        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = _version_probe("nonexistent-binary-12345")
            assert result == ""


class TestHasProvenance:
    """Tests for _has_provenance helper."""

    def test_has_provenance_true(self):
        """UT-TOOLS-026: _has_provenance returns True when marker present."""
        from modules.tools.src.capabilities_tools_installer import _has_provenance
        from modules.shared.src.taxonomy_common_constant import PROVENANCE_MARKER
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sh") as f:
            f.write(f"#!/bin/bash\n# {PROVENANCE_MARKER}\necho hello\n")
            path = f.name

        try:
            from pathlib import Path
            result = _has_provenance(Path(path))
            assert result is True
        finally:
            Path(path).unlink()

    def test_has_provenance_false(self):
        """UT-TOOLS-027: _has_provenance returns False when marker absent."""
        from modules.tools.src.capabilities_tools_installer import _has_provenance
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sh") as f:
            f.write("#!/bin/bash\necho hello\n")
            path = f.name

        try:
            from pathlib import Path
            result = _has_provenance(Path(path))
            assert result is False
        finally:
            Path(path).unlink()

    def test_has_provenance_missing_file(self):
        """UT-TOOLS-028: _has_provenance returns False for missing file."""
        from modules.tools.src.capabilities_tools_installer import _has_provenance
        from pathlib import Path

        result = _has_provenance(Path("/nonexistent/file"))
        assert result is False
