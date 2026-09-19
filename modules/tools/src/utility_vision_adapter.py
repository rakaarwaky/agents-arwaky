"""Vision-arwaky adapter (uv venv) — unified install + update + teardown.

Creates a venv in ~/.local/share/vision-arwaky/venv/, pip-installs the
internal/vision-arwaky package, and symlinks the launchers into ~/.local/bin/.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_paths import bin_home
from modules.tools.src.utility_adapter_base import AdapterBase, ROOT
from modules.tools.src.utility_venv_helpers import (
    ensure_venv,
    install_package,
    setup_bin_links,
    setup_xdg_directories,
)

TOOL_NAME = "vision-arwaky"
SRC_REL = f"internal/{TOOL_NAME}"
LAUNCHERS = [
    ("vision-arwaky", "vision-arwaky-cli"),
    ("vision-arwaky-cli", "vision-arwaky-cli"),
    ("va", "vision-arwaky-cli"),
    ("vision-arwaky-mcp", "vision-arwaky-mcp"),
]


class VisionAdapter(AdapterBase):
    """Install/update internal/vision-arwaky via a uv-managed venv (XDG compliant)."""

    def satisfied(self, spec, root: Path | None = None) -> bool:
        return (bin_home() / "vision-arwaky").exists()

    # -- install (from old installer adapter, verbatim mechanics) ----------------
    def install(self, spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
        from modules.shared.src.taxonomy_xdg_paths import tool_data_dir

        root = root or ROOT
        src_dir = root / SRC_REL

        if not self.ensure_source(root, SRC_REL):
            raise FileNotFoundError(f"source not found {src_dir}")

        python_bin = ensure_venv(TOOL_NAME, force=False)
        install_package(python_bin, src_dir, TOOL_NAME)
        setup_xdg_directories(TOOL_NAME)
        setup_bin_links(python_bin, LAUNCHERS)

        print("\n>>> Successfully installed vision-arwaky")
        print(f"    Venv: {python_bin.parent}")
        print(f"    Data: {tool_data_dir(TOOL_NAME)}")
        print(f"    Run 'vision-arwaky-cli init' to setup workspace symlinks")
        return [python_bin]

    # -- update (from old updater adapter) ---------------------------------------
    def is_pin_satisfied(self, spec, root: Path) -> tuple[bool, str]:
        source = root / SRC_REL
        if not source.exists():
            return False, "submodule not initialized"
        return False, "venv/pip (rebuild required)"

    def update(self, spec, root: Path) -> list[Path]:
        from modules.shared.src.utility_git_update import update_submodule, write_install_stamp

        if not update_submodule(root, SRC_REL):
            raise ToolUpdateError(f"submodule update failed: {SRC_REL}")

        source = root / SRC_REL
        if not source.exists():
            raise ToolUpdateError(f"source not found {source}")

        print(f">>> Updating {TOOL_NAME} (XDG compliant)...")
        python_bin = ensure_venv(TOOL_NAME, force=True)
        install_package(python_bin, source, TOOL_NAME)
        setup_xdg_directories(TOOL_NAME)
        setup_bin_links(python_bin, LAUNCHERS)
        write_install_stamp(python_bin.parent.parent, TOOL_NAME, source)

        created = [bin_home() / name for name, _entry in LAUNCHERS]
        print(f"\n>>> Successfully updated {TOOL_NAME}")
        print(f"    Venv: {python_bin.parent}")
        return created

    # -- teardown data --------------------------------------------------------------
    def owned_paths(self, spec, root: Path | None = None) -> list[Path]:
        return self.generic_owned(spec, [name for name, _e in LAUNCHERS])
