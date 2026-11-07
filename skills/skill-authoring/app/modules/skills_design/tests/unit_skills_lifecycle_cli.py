"""Unit tests for flat lifecycle CLI commands through ``cmd_skills``."""

from __future__ import annotations

from pathlib import Path

from cli.src.surface_skills_command import cmd_skills
from shared.src.skills_design.taxonomy_skills_response import SkillsExitCode

from skills_design.src.root_skills_container import default_aggregate
from skills_design.tests.fixture_skills import clean_tree

def _setup_pack_with_skill(tmp_path: Path, skill_name: str = "lifecycle_alpha") -> Path:
    root = clean_tree(tmp_path)
    skill_dir = root / "cat" / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("# Test Skill\n", encoding="utf-8")
    return root

def test_cmd_skills_lifecycle_help(capsys) -> None:
    aggregate = default_aggregate()
    code = cmd_skills(["status", "--help"], aggregate)
    assert code == 0

def test_cmd_skills_unknown_lifecycle_subcommand(capsys) -> None:
    aggregate = default_aggregate()
    code = cmd_skills(["invalid_subcommand"], aggregate)
    assert code == SkillsExitCode.USAGE_ERROR
    captured = capsys.readouterr()
    assert "Unknown skills subcommand" in captured.err

def test_lifecycle_cli_status(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path)
    aggregate = default_aggregate(default_root=root)
    code = cmd_skills(["status"], aggregate)
    assert code == 0
    captured = capsys.readouterr()
    assert "[OK] status" in captured.out

def test_lifecycle_cli_usage(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path)
    aggregate = default_aggregate(default_root=root)
    code = cmd_skills(["usage"], aggregate)
    assert code == 0
    captured = capsys.readouterr()
    assert "[OK] usage" in captured.out

def test_lifecycle_cli_pause_and_resume(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path)
    aggregate = default_aggregate(default_root=root)

    code_pause = cmd_skills(["pause"], aggregate)
    assert code_pause == 0
    assert "[OK] lifecycle paused" in capsys.readouterr().out

    code_resume = cmd_skills(["resume"], aggregate)
    assert code_resume == 0
    assert "[OK] lifecycle resumed" in capsys.readouterr().out

def test_lifecycle_cli_pin_and_unpin(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    aggregate = default_aggregate(default_root=root)

    code_pin = cmd_skills(["pin", "alpha"], aggregate)
    assert code_pin == 0
    assert "[OK] pin" in capsys.readouterr().out

    code_unpin = cmd_skills(["unpin", "alpha"], aggregate)
    assert code_unpin == 0
    assert "[OK] unpin" in capsys.readouterr().out

def test_lifecycle_cli_lock_and_unlock(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    aggregate = default_aggregate(default_root=root)

    code_lock = cmd_skills(["lock", "alpha"], aggregate)
    assert code_lock == 0
    assert "[OK] lock" in capsys.readouterr().out

    code_unlock = cmd_skills(["unlock", "alpha"], aggregate)
    assert code_unlock == 0
    assert "[OK] unlock" in capsys.readouterr().out

def test_lifecycle_cli_archive_and_restore(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    aggregate = default_aggregate(default_root=root)

    code_archive = cmd_skills(["archive", "alpha", "--apply"], aggregate)
    assert code_archive == 0
    captured = capsys.readouterr()
    assert "[APPLIED] archive/restore" in captured.out

    code_restore = cmd_skills(["restore", "alpha", "--apply"], aggregate)
    assert code_restore == 0
    captured = capsys.readouterr()
    assert "[APPLIED] archive/restore" in captured.out

def test_lifecycle_cli_list_unmanaged_and_archived(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    aggregate = default_aggregate(default_root=root)

    code_unmanaged = cmd_skills(["list-unmanaged"], aggregate)
    assert code_unmanaged == 0
    assert "[OK] list-unmanaged" in capsys.readouterr().out

    cmd_skills(["archive", "alpha"], aggregate)
    capsys.readouterr()  # clear buffer

    code_archived = cmd_skills(["list-archived"], aggregate)
    assert code_archived == 0
    assert "[OK] list-archived" in capsys.readouterr().out

def test_lifecycle_cli_prune(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    aggregate = default_aggregate(default_root=root)
    code = cmd_skills(["prune", "--days", "30"], aggregate)
    assert code == 0
    assert "prune" in capsys.readouterr().out

def test_lifecycle_cli_purge(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    aggregate = default_aggregate(default_root=root)
    cmd_skills(["archive", "alpha"], aggregate)
    capsys.readouterr()

    code = cmd_skills(["purge", "--days", "0"], aggregate)
    assert code == 0
    assert "[OK] purge" in capsys.readouterr().out

def test_lifecycle_cli_adopt(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    aggregate = default_aggregate(default_root=root)
    code = cmd_skills(["adopt", "alpha"], aggregate)
    assert code == 0
    assert "[OK] adopt" in capsys.readouterr().out

def test_lifecycle_cli_backup_and_rollback(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    aggregate = default_aggregate(default_root=root)

    code_backup = cmd_skills(["backup"], aggregate)
    assert code_backup == 0
    assert "[OK] backup" in capsys.readouterr().out

    code_rollback = cmd_skills(["rollback"], aggregate)
    assert code_rollback == 0
    assert "[OK] rollback" in capsys.readouterr().out

def test_lifecycle_cli_ledger(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    aggregate = default_aggregate(default_root=root)
    code = cmd_skills(["ledger"], aggregate)
    assert code == 0
    assert "[OK] ledger" in capsys.readouterr().out

def test_lifecycle_cli_run(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path)
    aggregate = default_aggregate(default_root=root)
    code = cmd_skills(["run"], aggregate)
    assert code == 0
    assert "[OK] run" in capsys.readouterr().out

def test_lifecycle_cli_ledger_compact(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path)
    aggregate = default_aggregate(default_root=root)
    code = cmd_skills(["ledger", "--compact"], aggregate)
    assert code == 0
    assert "[OK] ledger" in capsys.readouterr().out

def test_lifecycle_cli_missing_required_arg_returns_usage(capsys) -> None:
    """Verbs with a required positional must return exit code 2 on missing arg."""
    aggregate = default_aggregate()
    code = cmd_skills(["pin"], aggregate)
    assert code == SkillsExitCode.USAGE_ERROR
