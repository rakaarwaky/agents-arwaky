"""Check feature — public symbols.

Re-exports the orchestrator, container, the 5 check runners, and the
surface entry point so feature consumers can import from
``modules.check`` directly.
"""
from __future__ import annotations

from modules.check.src.agent_check_orchestrator import CheckOrchestrator
from modules.check.src.capabilities_check_docs import DocsCheckRunner
from modules.check.src.capabilities_check_json import JsonCheckRunner
from modules.check.src.capabilities_check_python import PythonCheckRunner
from modules.check.src.capabilities_check_shell import ShellCheckRunner
from modules.check.src.capabilities_check_skills import SkillsCheckRunner
from modules.check.src.root_check_container import CheckContainer, create_check_feature
from modules.cli.src.surface_check_command import cmd_check

__all__ = [
    "CheckContainer",
    "CheckOrchestrator",
    "DocsCheckRunner",
    "JsonCheckRunner",
    "PythonCheckRunner",
    "ShellCheckRunner",
    "SkillsCheckRunner",
    "cmd_check",
    "create_check_feature",
]
