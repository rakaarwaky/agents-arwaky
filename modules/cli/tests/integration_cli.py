"""Integration tests for the shared CLI surface package."""
from __future__ import annotations

import json
from pathlib import Path


def test_cli_packages_import_and_config_surface_executes(tmp_path: Path, capsys) -> None:
    """CLI-03/04: package modules exist and a surface verb reaches the aggregate."""
    import modules.cli
    import modules.cli.src
    from modules.cli.src.surface_config_command import ConfigCommand, cmd_config
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.config.src.capabilities_config_modifier import ConfigModifier
    from modules.config.src.capabilities_config_writer import ConfigWriter

    assert modules.cli is not None
    assert modules.cli.src is not None

    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"mcpServers": {"alpha": {"command": "node"}}}), encoding="utf-8")
    aggregate = ConfigOrchestrator(ConfigWriter(), ConfigModifier())
    surface = ConfigCommand(aggregate)

    assert cmd_config(["inspect", str(path)], surface) == 0
    inspected = capsys.readouterr().out
    assert '"alpha"' in inspected
    assert cmd_config(["load", str(path)], surface) == 0
    loaded = capsys.readouterr().out
    assert '"command": "node"' in loaded


def test_root_help_advertises_local_backup_only(capsys) -> None:
    """The root help exposes no external backup destination or transport."""
    from modules.root_cli_entry import cmd_help

    assert cmd_help([]) == 0
    output = capsys.readouterr().out
    assert "Create local backups of tool data" in output
    assert "Google Drive" not in output
    assert "gdrive" not in output
    assert "cloud backup" not in output.lower()
