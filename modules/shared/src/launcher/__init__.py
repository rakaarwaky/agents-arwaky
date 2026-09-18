"""Launcher value objects + contract (P4-A3).\n\nMoved from common.launcher.\n"""
from __future__ import annotations

from modules.shared.src.launcher.contract_launcher_protocol import ILauncherWriter
from modules.shared.src.launcher.taxonomy_launcher_vo import LauncherSpec

__all__ = [
    "ILauncherWriter",
    "LauncherSpec",
]
