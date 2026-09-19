"""Vision-arwaky adapter (uv venv) — verbatim port of tools/install/install_vision.py.

Creates a venv in ~/.local/share/vision-arwaky/venv/, pip-installs the
internal/vision-arwaky package, and symlinks the launchers into ~/.local/bin/.
"""
from __future__ import annotations

from pathlib import Path

from modules.installer.src.utility_adapter_base import AdapterBase, ROOT
from modules.installer.src.utility_venv_helpers import (
    ensure_venv,
    install_package,
    setup_xdg_directories,
    setup_bin_links,
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
    """Install internal/vision-arwaky via a uv-managed venv (XDG compliant)."""

    def satisfied(self, spec, root: Path | None = None) -> bool:
        from modules.shared.src.taxonomy_xdg_paths import bin_home
        return (bin_home() / "vision-arwaky").exists()

    def install(self, spec: ToolSpec, root: Path = ROOT, *, daemons=None) -> list[Path]:
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
