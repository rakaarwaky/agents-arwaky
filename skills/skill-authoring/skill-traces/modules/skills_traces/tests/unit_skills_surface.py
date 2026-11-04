"""Unit tests for the ``aa skills`` surface (argv → request → render)."""

from __future__ import annotations

from pathlib import Path

from skills_design.tests.fixture_skills import (
    clean_tree,
    crafted_tree,
    run_surface,
)

from skills_design.src.surface_skills_command import cmd_skills


def test_unknown_subcommand_exits_2(capsys) -> None:
    """Flagged change: ``aa skills <unknown>`` is a usage error (2)."""
    from skills_design.src.root_skills_container import default_aggregate

    code = cmd_skills(["frobnicate"], default_aggregate())
    assert code == 2
    captured = capsys.readouterr()
    assert "Unknown skills subcommand: frobnicate" in captured.err


def test_bare_skills_prints_usage_and_exits_0(capsys) -> None:
    """The historical no-argument behavior is preserved."""
    from skills_design.src.root_skills_container import default_aggregate

    assert cmd_skills([], default_aggregate()) == 0
    captured = capsys.readouterr()
    assert "aa skills list" in captured.out


def test_argparse_errors_exit_2(tmp_path: Path) -> None:
    """A discover without a query is a usage error (2)."""
    root = crafted_tree(tmp_path)
    code, _out, err = run_surface(root, "discover")
    assert code == 2
    assert "the following arguments are required" in err


def test_lint_reports_issues_and_exits_1(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    code, out, _ = run_surface(root, "lint")
    assert code == 1
    assert "1 lint issue(s) found" in out


def test_lint_filters_narrow_without_hiding_the_total(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    code, out, _ = run_surface(root, "lint", "--category", "notes")
    assert code == 1
    assert "1 lint issue(s) found (0 in scope category=notes):" in out


def test_lint_clean_pack_exits_0(tmp_path: Path) -> None:
    root = clean_tree(tmp_path)
    code, out, _ = run_surface(root, "lint")
    assert code == 0
    assert "No lint issues found." in out


def test_catalog_default_builds_and_prints(tmp_path: Path) -> None:
    """Neither flag → build + read (the convenient agent default)."""
    root = crafted_tree(tmp_path)
    code, out, _ = run_surface(root, "catalog")
    assert code == 0
    assert "Rebuilt" in out
    assert "Categories:" in out
    # the full catalog text follows the rebuild lines
    assert "## Skills" in out


def test_catalog_build_only_prints_counts(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    code, out, _ = run_surface(root, "catalog", "--build")
    assert code == 0
    assert "Rebuilt" in out
    # build only: no catalog body is printed
    assert "## Skills" not in out


def test_catalog_read_only_prints_content(tmp_path: Path) -> None:
    """--read alone prints the existing CATALOG.md without rebuilding."""
    root = crafted_tree(tmp_path)
    # build first so the file exists
    run_surface(root, "catalog", "--build")
    code, out, _ = run_surface(root, "catalog", "--read")
    assert code == 0
    assert "## Skills" in out
    # no rebuild happened in this invocation
    assert "Rebuilt" not in out


def test_catalog_read_missing_file_exits_1(tmp_path: Path) -> None:
    """--read alone with no CATALOG.md exits 1 with a clear message."""
    root = crafted_tree(tmp_path)  # no CATALOG.md yet
    code, _out, err = run_surface(root, "catalog", "--read")
    assert code == 1
    assert "CATALOG.md not found" in err


def test_catalog_build_then_read(tmp_path: Path) -> None:
    """--build --read: rebuild counts line followed by the full content."""
    root = crafted_tree(tmp_path)
    code, out, _ = run_surface(root, "catalog", "--build", "--read")
    assert code == 0
    assert "Rebuilt" in out
    assert "## Skills" in out


def test_mutating_commands_in_cli_preview(tmp_path: Path) -> None:
    """move / archive / create preview a plan (exit 0) without --apply.

    ``traces`` has its own surface file; it is not routed from ``cmd_skills``.
    """
    root = crafted_tree(tmp_path)
    for args in (
        ("move", "drafts/doc-drafts", "notes"),
        ("archive", "drafts/doc-drafts"),
        ("create", "skill", "drafts/doc-drafts", "--category", "notes"),
    ):
        code, out, _ = run_surface(root, *args)
        assert code == 0, args
        assert "Plan" in out or "dry-run" in out, (args, out)

    # traces is now routed from cmd_skills to the traces surface.
    code, _out, _err = run_surface(root, "traces")
    assert code == 2  # no sub-action → usage error from cmd_traces


def test_discover_empty_query_is_a_usage_error(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    code, _out, err = run_surface(root, "discover", "")
    assert code == 2
    assert err == "ERROR: Query is empty\n"


def test_lint_full_listing_matches_the_legacy_shape(tmp_path: Path) -> None:
    """The per-issue listing keeps the ``- [type] locator: message`` lines."""
    root = crafted_tree(tmp_path)
    code, out, _ = run_surface(root, "lint")
    assert code == 1
    assert "1 lint issue(s) found" in out
    assert "[name-mismatch]" in out


def test_discover_no_match_prints_the_legacy_line(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    run_surface(root, "catalog")
    code, out, _ = run_surface(root, "discover", "no-such-skill-zzz")
    assert code == 0
    assert out == "No matching skills found in CATALOG.md.\n"


def test_discover_with_matches_prints_the_score_table(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    run_surface(root, "catalog")
    code, out, _ = run_surface(root, "discover", "notes")
    assert code == 0
    assert "| Skill | Category | Description | Path | Score |" in out
    assert "note-taker" in out


def test_list_and_read_keep_their_output_shape(tmp_path: Path) -> None:
    """The read-only surface is byte-stable."""
    root = clean_tree(tmp_path)

    code, out, _ = run_surface(root, "list")
    assert code == 0
    assert "SKILL" in out
    assert "1 skills in the pack." in out

    code, out, _ = run_surface(root, "read", "alpha")
    assert code == 0
    assert out.startswith("---\nname: alpha")

    code, out, _ = run_surface(root, "read", "nope")
    assert code == 1
