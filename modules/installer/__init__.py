"""Installer feature — per-tool install capabilities + orchestrator (AES)."""
from modules.installer.src.agent_installer_orchestrator import InstallerOrchestrator
from modules.installer.src.capabilities_blender_installer import BlenderInstaller
from modules.installer.src.capabilities_vision_installer import VisionInstaller
from modules.installer.src.capabilities_qwen_web_installer import QwenWebInstaller
from modules.installer.src.capabilities_lint_installer import LintInstaller
from modules.installer.src.capabilities_context7_installer import Context7Installer
from modules.installer.src.capabilities_fetch_installer import FetchInstaller
from modules.installer.src.capabilities_ponytail_installer import PonytailInstaller
from modules.installer.src.capabilities_anytype_installer import AnytypeInstaller
from modules.installer.src.capabilities_anytype_daemon_installer import AnytypeDaemonInstaller
from modules.installer.src.capabilities_codegraph_installer import CodegraphInstaller
from modules.installer.src.capabilities_ninerouter_installer import NinerouterInstaller
from modules.installer.src.capabilities_workspace_installer import WorkspaceInstaller
from modules.installer.src.capabilities_mnemosyne_installer import MnemosyneInstaller
from modules.installer.src.capabilities_skill_installer import SkillInstaller

__all__ = [
    "AnytypeDaemonInstaller",
    "AnytypeInstaller",
    "BlenderInstaller",
    "CodegraphInstaller",
    "Context7Installer",
    "FetchInstaller",
    "InstallerOrchestrator",
    "LintInstaller",
    "MnemosyneInstaller",
    "NinerouterInstaller",
    "PonytailInstaller",
    "QwenWebInstaller",
    "SkillInstaller",
    "VisionInstaller",
    "WorkspaceInstaller",
]
