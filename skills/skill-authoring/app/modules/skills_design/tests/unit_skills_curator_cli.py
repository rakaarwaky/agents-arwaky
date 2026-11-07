"""Unit and integration tests for PR 7: Curator CLI surface."""

from __future__ import annotations

from pathlib import Path

from cli.src.surface_skills_command import cmd_skills
from cli.src.surface_skills_curator_command import cmd_skills_curator
from shared.src.skills_design.taxonomy_skills_response import SkillsExitCode

from skills_design.src.root_skills_container import default_aggregate
from skills_design.tests.fixture_skills import clean_tree


def _setup_pack_with_skill(tmp_path: Path, skill_name: str = "curated_alpha") -> Path:
    root = clean_tree(tmp_path)
    skill_dir = root / "cat" / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("# Test Skill\n", encoding="utf-8")
    return root


# ─── Top-level cmd_skills delegation to curator ─────────────────────

def test_cmd_skills_delegates_to_curator_help(capsys) -> None:
    aggregate = default_aggregate()
    code = cmd_skills(["curator", "--help"], aggregate)
    assert code == 0
    captured = capsys.readouterr()
    assert "Curator (agent-level):" in captured.out


def test_cmd_skills_unknown_curator_subcommand(capsys) -> None:
    aggregate = default_aggregate()
    code = cmd_skills(["curator", "invalid_subcommand"], aggregate)
    assert code == SkillsExitCode.USAGE_ERROR
    captured = capsys.readouterr()
    assert "Unknown curator subcommand" in captured.err


# ─── Individual curator CLI verb tests ──────────────────────────────

def test_curator_cli_status(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path)
    aggregate = default_aggregate(default_root=root)
    code = cmd_skills_curator(["status"], aggregate)
    assert code == 0
    captured = capsys.readouterr()
    assert "[OK] curator status" in captured.out


def test_curator_cli_usage(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path)
    aggregate = default_aggregate(default_root=root)
    code = cmd_skills_curator(["usage"], aggregate)
    assert code == 0
    captured = capsys.readouterr()
    assert "[OK] curator usage" in captured.out


def test_curator_cli_pause_and_resume(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path)
    aggregate = default_aggregate(default_root=root)

    code_pause = cmd_skills_curator(["pause"], aggregate)
    assert code_pause == 0
    assert "[OK] curator paused" in capsys.readouterr().out

    code_resume = cmd_skills_curator(["resume"], aggregate)
    assert code_resume == 0
    assert "[OK] curator resumed" in capsys.readouterr().out


def test_curator_cli_pin_and_unpin(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    aggregate = default_aggregate(default_root=root)

    code_pin = cmd_skills_curator(["pin", "alpha"], aggregate)
    assert code_pin == 0
    assert "[OK] curator pin" in capsys.readouterr().out

    code_unpin = cmd_skills_curator(["unpin", "alpha"], aggregate)
    assert code_unpin == 0
    assert "[OK] curator unpin" in capsys.readouterr().out


def test_curator_cli_lock_and_unlock(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    aggregate = default_aggregate(default_root=root)

    code_lock = cmd_skills_curator(["lock", "alpha"], aggregate)
    assert code_lock == 0
    assert "[OK] curator lock" in capsys.readouterr().out

    code_unlock = cmd_skills_curator(["unlock", "alpha"], aggregate)
    assert code_unlock == 0
    assert "[OK] curator unlock" in capsys.readouterr().out


def test_curator_cli_archive_and_restore(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    aggregate = default_aggregate(default_root=root)

    code_archive = cmd_skills_curator(["archive", "alpha"], aggregate)
    assert code_archive == 0
    assert "[APPLIED] curator archive/restore" in capsys.readouterr().out

    code_restore = cmd_skills_curator(["restore", "alpha"], aggregate)
    assert code_restore == 0
    assert "[APPLIED] curator archive/restore" in capsys.readouterr().out


def test_curator_cli_list_unmanaged_and_archived(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    aggregate = default_aggregate(default_root=root)

    code_unmanaged = cmd_skills_curator(["list-unmanaged"], aggregate)
    assert code_unmanaged == 0
    assert "[OK] curator list-unmanaged" in capsys.readouterr().out

    cmd_skills_curator(["archive", "alpha"], aggregate)
    capsys.readouterr()  # clear buffer

    code_archived = cmd_skills_curator(["list-archived"], aggregate)
    assert code_archived == 0
    assert "[OK] curator list-archived" in capsys.readouterr().out


def test_curator_cli_prune(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    aggregate = default_aggregate(default_root=root)
    code = cmd_skills_curator(["prune", "--days", "30", "-y"], aggregate)
    assert code == 0
    assert "[OK] curator prune" in capsys.readouterr().out


def test_curator_cli_purge(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    aggregate = default_aggregate(default_root=root)
    cmd_skills_curator(["archive", "alpha"], aggregate)
    capsys.readouterr()

    code = cmd_skills_curator(["purge", "alpha"], aggregate)
    assert code == 0
    assert "[OK] curator purge" in capsys.readouterr().out


def test_curator_cli_adopt(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    aggregate = default_aggregate(default_root=root)
    code = cmd_skills_curator(["adopt", "alpha"], aggregate)
    assert code == 0
    assert "[OK] curator adopt" in capsys.readouterr().out


def test_curator_cli_backup_and_rollback(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    aggregate = default_aggregate(default_root=root)

    code_backup = cmd_skills_curator(["backup"], aggregate)
    assert code_backup == 0
    assert "[OK] curator backup" in capsys.readouterr().out

    code_rollback = cmd_skills_curator(["rollback"], aggregate)
    assert code_rollback == 0
    assert "[OK] curator rollback" in capsys.readouterr().out


def test_curator_cli_ledger(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    aggregate = default_aggregate(default_root=root)
    code = cmd_skills_curator(["ledger"], aggregate)
    assert code == 0
    assert "[OK] curator ledger" in capsys.readouterr().out


# ─── Missing verb + negative path coverage ──────────────────────────

def test_curator_cli_run(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path)
    aggregate = default_aggregate(default_root=root)
    code = cmd_skills_curator(["run"], aggregate)
    assert code == 0
    assert "[OK] curator run" in capsys.readouterr().out


def test_curator_cli_ledger_compact(tmp_path: Path, capsys) -> None:
    root = _setup_pack_with_skill(tmp_path)
    aggregate = default_aggregate(default_root=root)
    code = cmd_skills_curator(["ledger", "--compact"], aggregate)
    assert code == 0
    assert "[OK] curator ledger" in capsys.readouterr().out


def test_curator_cli_missing_required_arg_returns_usage(capsys) -> None:
    """Verbs with a required positional must return exit code 2 on missing arg."""
    aggregate = default_aggregate()
    code = cmd_skills_curator(["pin"], aggregate)
    assert code == SkillsExitCode.USAGE_ERROR


def test_curator_cli_unknown_skill_failure_path(tmp_path: Path, capsys) -> None:
    """Unknown skill returns non-ok and exit code 1 via aggregate result."""
    root = _setup_pack_with_skill(tmp_path)
    aggregate = default_aggregate(default_root=root)
    code = cmd_skills_curator(["pin", "nonexistent"], aggregate)
    assert code == SkillsExitCode.ISSUES_FOUND
    captured = capsys.readouterr()
    assert "ERROR:" in captured.err or "Skill not found" in captured.err


def test_curator_cli_prune_dry_run_prefix(tmp_path: Path, capsys) -> None:
    """Dry-run prune prints [DRY-RUN] status prefix."""
    root = _setup_pack_with_skill(tmp_path)
    aggregate = default_aggregate(default_root=root)
    code = cmd_skills_curator(["prune", "--days", "30", "--dry-run"], aggregate)
    assert code == 0
    captured = capsys.readouterr()
    assert "[DRY-RUN] curator prune" in captured.out

