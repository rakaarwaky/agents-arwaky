"""Unit tests for modules/tools — capability classes and helper functions."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from modules.shared.src.taxonomy_common_vo import ToolSpec
from modules.shared.src.utility_tool_mechanics import ROOT


def _spec(id: str = "test-tool") -> ToolSpec:
    """A manifest spec for a tool id that no adapter unit owns."""
    return ToolSpec(
        id=id,
        category="dev",
        binary="test",
        is_mcp=False,
        description="test",
        path="/test",
        alias=None,
        mcp_binary=None,
        runner="",
    )


class TestInstallerCapability:
    """Tests for InstallerCapability."""

    def test_init_with_defaults(self):
        """UT-TOOLS-001: InstallerCapability initializes with defaults."""
        from modules.tools.src.capabilities_tools_installer import InstallerCapability

        installer = InstallerCapability()
        assert installer._root is None
        assert installer._daemons is None
        assert installer._registry == {}

    def test_init_with_params(self):
        """UT-TOOLS-002: InstallerCapability initializes with explicit params."""
        from modules.tools.src.capabilities_tools_installer import InstallerCapability

        root = Path("/test/root")
        daemons = MagicMock()
        registry = {"test-tool": MagicMock()}
        installer = InstallerCapability(root=root, daemons=daemons, registry=registry)

        assert installer._root == root
        assert installer._daemons is daemons
        assert installer._registry == registry

    def test_has_no_execute_bag(self):
        """UT-TOOLS-003: the installer exposes install(), never execute(op)."""
        from modules.tools.src.capabilities_tools_installer import InstallerCapability

        assert not hasattr(InstallerCapability, "execute")
        assert callable(InstallerCapability.install)

    def test_install_returns_result(self):
        """UT-TOOLS-004: install(spec) returns an InstallResult."""
        from modules.shared.src.taxonomy_common_vo import InstallResult
        from modules.tools.src.capabilities_tools_installer import InstallerCapability

        installer = InstallerCapability(registry={"test-tool": MagicMock()})
        result = installer.install(_spec())
        assert isinstance(result, InstallResult)

    def test_missing_registry_raises(self):
        """UT-TOOLS-005: install without a wired registry raises ToolInstallError."""
        from modules.shared.src.taxonomy_common_error import ToolInstallError
        from modules.tools.src.capabilities_tools_installer import InstallerCapability

        installer = InstallerCapability()
        with patch.dict("os.environ", {}, clear=True):
            try:
                installer.install(_spec())
                raise AssertionError("Should have raised ToolInstallError")
            except ToolInstallError:
                pass

    def test_dry_run_returns_result(self):
        """UT-TOOLS-006: dry-run returns InstallResult without side effects."""
        from modules.tools.src.capabilities_tools_installer import InstallerCapability

        installer = InstallerCapability(registry={"test-tool": MagicMock()})
        result = installer.install(_spec(), dry_run=True)
        assert result.success is True
        assert "[dry-run]" in result.message


class TestUpdaterCapability:
    """Tests for UpdaterCapability."""

    def test_init_with_defaults(self):
        """UT-TOOLS-008: UpdaterCapability initializes with defaults."""
        from modules.tools.src.capabilities_tools_updater import UpdaterCapability

        updater = UpdaterCapability()
        assert updater._root is None
        assert updater._registry == {}

    def test_init_with_params(self):
        """UT-TOOLS-009: UpdaterCapability initializes with explicit params."""
        from modules.tools.src.capabilities_tools_updater import UpdaterCapability

        root = Path("/test/root")
        registry = {"test-tool": MagicMock()}
        updater = UpdaterCapability(root=root, registry=registry)

        assert updater._root == root
        assert updater._registry == registry

    def test_has_no_execute_bag(self):
        """UT-TOOLS-010: the updater exposes update(), never execute(op)."""
        from modules.tools.src.capabilities_tools_updater import UpdaterCapability

        assert not hasattr(UpdaterCapability, "execute")
        assert callable(UpdaterCapability.update)

    def test_update_returns_result(self):
        """UT-TOOLS-011: update(spec) returns an UpdateResult."""
        from modules.shared.src.taxonomy_common_vo import UpdateResult
        from modules.tools.src.capabilities_tools_updater import UpdaterCapability

        registry = {"test-tool": MagicMock()}
        registry["test-tool"].is_pin_satisfied.return_value = (False, "outdated")
        updater = UpdaterCapability(registry=registry)
        result = updater.update(_spec())
        assert isinstance(result, UpdateResult)

    def test_missing_registry_raises(self):
        """UT-TOOLS-012: update without a wired registry raises ToolUpdateError."""
        from modules.shared.src.taxonomy_common_error import ToolUpdateError
        from modules.tools.src.capabilities_tools_updater import UpdaterCapability

        updater = UpdaterCapability()
        try:
            updater.update(_spec())
            raise AssertionError("Should have raised ToolUpdateError")
        except ToolUpdateError:
            pass

    def test_dry_run_returns_result(self):
        """UT-TOOLS-013: dry-run returns UpdateResult without side effects."""
        from modules.tools.src.capabilities_tools_updater import UpdaterCapability

        registry = {"test-tool": MagicMock()}
        registry["test-tool"].is_pin_satisfied.return_value = (False, "outdated")
        updater = UpdaterCapability(registry=registry)
        result = updater.update(_spec(), dry_run=True)
        assert result.success is True
        assert "[dry-run]" in result.message


class TestUninstallerCapability:
    """Tests for UninstallerCapability."""

    def test_init_with_defaults(self):
        """UT-TOOLS-014: UninstallerCapability initializes with defaults."""
        from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability

        uninstaller = UninstallerCapability()
        assert uninstaller._daemons is None

    def test_init_with_daemons(self):
        """UT-TOOLS-015: UninstallerCapability initializes with daemons."""
        from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability

        daemons = MagicMock()
        uninstaller = UninstallerCapability(daemons=daemons)
        assert uninstaller._daemons == daemons

    def test_has_no_execute_bag(self):
        """UT-TOOLS-016: the uninstaller exposes uninstall(), never execute(op)."""
        from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability

        assert not hasattr(UninstallerCapability, "execute")
        assert callable(UninstallerCapability.uninstall)

    def test_uninstall_returns_result(self):
        """UT-TOOLS-017: uninstall(spec) returns an UninstallResult."""
        from modules.shared.src.taxonomy_common_vo import UninstallResult
        from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability

        uninstaller = UninstallerCapability()
        result = uninstaller.uninstall(_spec())
        assert isinstance(result, UninstallResult)

    def test_uninstall_tolerates_missing_owned_paths(self):
        """UT-TOOLS-018: uninstall(spec) works with owned_paths omitted."""
        from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability

        uninstaller = UninstallerCapability()
        result = uninstaller.uninstall(_spec(), None)
        assert result is not None


class TestRunnerCapability:
    """Tests for RunnerCapability."""

    def test_init_with_defaults(self):
        """UT-TOOLS-019: RunnerCapability initializes with defaults."""
        from modules.tools.src.capabilities_tools_runner import RunnerCapability

        runner = RunnerCapability()
        assert runner._root is None

    def test_init_with_root(self):
        """UT-TOOLS-020: RunnerCapability initializes with explicit root."""
        from modules.tools.src.capabilities_tools_runner import RunnerCapability

        root = Path("/test/root")
        runner = RunnerCapability(root=root)
        assert runner._root == root

    def test_has_no_execute_bag(self):
        """UT-TOOLS-021: the runner exposes run() and discover(), never execute(op)."""
        from modules.tools.src.capabilities_tools_runner import RunnerCapability

        assert not hasattr(RunnerCapability, "execute")
        assert callable(RunnerCapability.run)
        assert callable(RunnerCapability.discover)

    def test_run_returns_exit_code(self):
        """UT-TOOLS-022: run(spec, args) returns an exit code."""
        from modules.tools.src.capabilities_tools_runner import RunnerCapability

        runner = RunnerCapability()
        result = runner.run(_spec(), [])
        assert isinstance(int(result), int)

    def test_discover_returns_path_or_none(self):
        """UT-TOOLS-023: discover(spec) returns a Path or None."""
        from modules.tools.src.capabilities_tools_runner import RunnerCapability

        runner = RunnerCapability()
        result = runner.discover(_spec())
        assert result is None or isinstance(result, Path)


class TestAdapterCapabilities:
    """Tests for the per-tool adapter capabilities."""

    ADAPTERS = (
        ("anytype", "AnytypeToolsAdapter"),
        ("blender", "BlenderToolsAdapter"),
        ("codegraph", "CodegraphToolsAdapter"),
        ("context7", "Context7ToolsAdapter"),
        ("fetch", "FetchToolsAdapter"),
        ("lint", "LintToolsAdapter"),
        ("mnemosyne", "MnemosyneToolsAdapter"),
        ("ninerouter", "NinerouterToolsAdapter"),
        ("ponytail", "PonytailToolsAdapter"),
        ("qwen_web", "QwenWebToolsAdapter"),
        ("vision", "VisionToolsAdapter"),
        ("workspace", "WorkspaceToolsAdapter"),
    )

    def test_each_implements_adapter_protocol(self):
        """UT-TOOLS-024: every provider adapter implements IToolsAdapterProtocol."""
        from importlib import import_module

        from modules.shared.src.contract_tools_protocol import IToolsAdapterProtocol

        for module_name, class_name in self.ADAPTERS:
            module = import_module(f"modules.tools.src.capabilities_tools_{module_name}_adapter")
            cls = getattr(module, class_name)
            assert issubclass(cls, IToolsAdapterProtocol), class_name

    def test_each_exposes_rich_methods(self):
        """UT-TOOLS-025: every provider adapter exposes the five named methods."""
        from importlib import import_module

        for module_name, class_name in self.ADAPTERS:
            module = import_module(f"modules.tools.src.capabilities_tools_{module_name}_adapter")
            adapter = getattr(module, class_name)()
            for method in ("satisfied", "is_pin_satisfied", "owned_paths", "install", "update"):
                assert callable(getattr(adapter, method)), f"{class_name}.{method}"
            assert not hasattr(adapter, "execute"), class_name

    def test_unknown_spec_raises_typed_error(self):
        """UT-TOOLS-026: an unowned spec id raises ToolUpdateError."""
        from importlib import import_module

        from modules.shared.src.taxonomy_common_error import ToolUpdateError

        module = import_module("modules.tools.src.capabilities_tools_lint_adapter")
        adapter = module.LintToolsAdapter()
        try:
            adapter.owned_paths(_spec())
            raise AssertionError("Should have raised ToolUpdateError")
        except ToolUpdateError:
            pass

    def test_unknown_spec_raises_typed_error_for_every_adapter(self):
        """UT-TOOLS-032: every adapter raises ToolUpdateError, never NameError."""
        from importlib import import_module

        from modules.shared.src.taxonomy_common_error import ToolUpdateError

        for module_name, class_name in self.ADAPTERS:
            module = import_module(f"modules.tools.src.capabilities_tools_{module_name}_adapter")
            adapter = getattr(module, class_name)()
            for method in ("satisfied", "is_pin_satisfied", "owned_paths"):
                try:
                    getattr(adapter, method)(_spec())
                    raise AssertionError(f"{class_name}.{method} should have raised")
                except ToolUpdateError:
                    pass

    def test_owned_paths_resolves_own_unit(self):
        """UT-TOOLS-033: every adapter returns owned paths for the spec its unit owns."""
        from importlib import import_module

        for module_name, class_name in self.ADAPTERS:
            module = import_module(f"modules.tools.src.capabilities_tools_{module_name}_adapter")
            units = dict(module.ADAPTER_UNITS)
            tool_id = next(iter(units))
            adapter = getattr(module, class_name)(units=units)
            spec = _spec(id=tool_id)
            assert adapter.owned_paths(spec) == list(units[tool_id].owned_paths(spec, ROOT))
            assert isinstance(adapter.satisfied(spec), bool)
            ok, reason = adapter.is_pin_satisfied(spec)
            assert isinstance(ok, bool) and isinstance(reason, str)


class TestVersionProbe:
    """Tests for _version_probe helper."""

    def test_version_probe_success(self):
        """UT-TOOLS-027: _version_probe returns version string on success."""
        from unittest.mock import MagicMock, patch

        from modules.tools.src.capabilities_tools_installer import _version_probe

        mock_proc = MagicMock()
        mock_proc.stdout = "test-tool 1.2.3\n"
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc) as mock_run:
            result = _version_probe("test-tool")
            assert result == "test-tool 1.2.3"
            mock_run.assert_called_once()

    def test_version_probe_missing_binary(self):
        """UT-TOOLS-028: _version_probe returns empty on missing binary."""
        from unittest.mock import patch

        from modules.tools.src.capabilities_tools_installer import _version_probe

        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = _version_probe("nonexistent-binary-12345")
            assert result == ""


class TestHasProvenance:
    """Tests for _has_provenance helper."""

    def test_has_provenance_true(self):
        """UT-TOOLS-029: _has_provenance returns True when marker present."""
        import tempfile

        from modules.shared.src.taxonomy_common_constant import PROVENANCE_MARKER
        from modules.tools.src.capabilities_tools_installer import _has_provenance

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sh") as f:
            f.write(f"#!/bin/bash\n# {PROVENANCE_MARKER}\necho hello\n")
            path = f.name

        try:
            assert _has_provenance(Path(path)) is True
        finally:
            Path(path).unlink()

    def test_has_provenance_false(self):
        """UT-TOOLS-030: _has_provenance returns False when marker absent."""
        import tempfile

        from modules.tools.src.capabilities_tools_installer import _has_provenance

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sh") as f:
            f.write("#!/bin/bash\necho hello\n")
            path = f.name

        try:
            assert _has_provenance(Path(path)) is False
        finally:
            Path(path).unlink()

    def test_has_provenance_missing_file(self):
        """UT-TOOLS-031: _has_provenance returns False for missing file."""
        from modules.tools.src.capabilities_tools_installer import _has_provenance

        assert _has_provenance(Path("/nonexistent/file")) is False
