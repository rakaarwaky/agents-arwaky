"""Integration tests for the shared CLI surface package."""
from __future__ import annotations

import json
from pathlib import Path


def test_cli_packages_import_and_config_surface_executes(tmp_path: Path, capsys) -> None:
    """DS-CLI-003/004: package modules exist and a surface verb reaches the aggregate."""
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
    assert output.count("Create local backups of tool data") == 1

def test_root_dispatch_table_routes_both_gateway_verbs(monkeypatch) -> None:
    """DS-CLI-05: the root dispatcher routes aa 9router and aa omniroute separately."""
    from modules import root_cli_entry as entry

    calls: list[tuple[str, list[str]]] = []

    def fake_nine(argv):
        calls.append(("9router", argv))
        return 0

    def fake_omni(argv):
        calls.append(("omniroute", argv))
        return 0

    monkeypatch.setattr(entry, "cmd_9router", fake_nine)
    monkeypatch.setattr(entry, "cmd_omniroute", fake_omni)

    assert entry._dispatch(["9router", "status"]) == 0
    assert entry._dispatch(["omniroute", "status"]) == 0
    assert calls == [("9router", ["status"]), ("omniroute", ["status"])]

def test_surface_exposes_cmd_9router_alongside_cmd_omniroute() -> None:
    """CLI-06: the daemon surface exports cmd_9router next to cmd_omniroute."""
    from modules.cli.src import surface_daemon_command as surface

    assert "cmd_9router" in surface.__all__
    assert "cmd_omniroute" in surface.__all__
    assert callable(surface.cmd_9router)
    assert callable(surface.cmd_omniroute)

def test_daemon_help_advertises_9router(monkeypatch, capsys) -> None:
    """CLI-07: aa daemon help lists 9router without dropping omniroute."""
    from modules import root_cli_entry as entry

    assert entry.cmd_daemon(["help"]) == 0
    out = capsys.readouterr().out
    assert "9router" in out
    assert "omniroute" in out
