"""Venv-based installer/updater helpers (P4-A3).\n\nMoved from common.venv; XDG-atomic I/O comes from ``modules.shared.src.xdg``.\n"""
from __future__ import annotations

from modules.shared.src.common.taxonomy_core_error import (
    ArwakyError,
    ToolInstallError,
    ToolUpdateError,
)
from modules.shared.src.venv.contract_venv_protocol import IVenvInstaller
from modules.shared.src.venv.taxonomy_venv_vo import VenvInfo
from modules.shared.src.venv.utility_venv_installer import (
    ensure_bin_home,
    ensure_venv,
    get_venv_dir,
    get_venv_python,
    install_package,
    run,
    setup_bin_links,
    setup_xdg_directories,
)

__all__ = [
    "ArwakyError",
    "IVenvInstaller",
    "ToolInstallError",
    "ToolUpdateError",
    "VenvInfo",
    "ensure_bin_home",
    "ensure_venv",
    "get_venv_dir",
    "get_venv_python",
    "install_package",
    "run",
    "setup_bin_links",
    "setup_xdg_directories",
]
