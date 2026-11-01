"""Unit tests for the ``aa skills`` surface (argv → request → render)."""

from __future__ import annotations

import json
from pathlib import Path

from modules.cli.src.surface_skills_command import cmd_skills
from modules.skills.src.root_skills_container import default_aggregate
from modules.skills.tests.fixture_skills import (
    clean_tree,
    crafted_tree,
    run_surface,
)


def test_unknown_subcommand_exits_2(capsys) -> None:
    """Flagged change: ``aa skills <unknown>`` is a usage error (2)."""
    code = cmd_skills(["frobnicate"], default_aggregate())
    assert code == 2
    captured = capsys.readouterr()
    assert "Unknown skills subcommand: frobnicate" in captured.err


def test_bare_skills_prints_usage_and_exits_0(capsys) -> None:
    """The historical no-argument behavior is preserved."""
    assert cmd_skills([], default_aggregate()) == 0
    captured = capsys.readouterr()
    assert "aa skills list" in captured.out


def test_argparse_errors_exit_2(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    code, _out, err = run_surface(root, "discover")
    assert code == 2
    assert "the following arguments are required" in err


def test_skills_root_overrides_the_derived_root(tmp_path: Path) -> None:
    """``--skills-root`` routes every authoring command to a crafted tree."""
    root = crafted_tree(tmp_path)
    code, out, _ = run_surface(root, "validate")
    assert code == 1
    assert str(root) in out or "1 validation issue(s) found" in out


def test_validate_filters_narrow_without_hiding_the_total(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    code, out, _ = run_surface(root, "validate", "--category", "notes")
    assert code == 1
    assert "1 validation issue(s) found (0 in scope category=notes):" in out
    assert "(none in scope)" in out

    code, out, _ = run_surface(root, "validate", "--rules-only")
    assert code == 1
    assert "[name-mismatch]" in out


def test_validate_summary_line_is_derived(tmp_path: Path) -> None:
    root = clean_tree(tmp_path)
    code, out, _ = run_surface(root, "validate", "--summary")
    assert code == 0
    assert out.strip() == "0 issues / 1 skills / 1 categories"


def test_json_key_order_matches_the_legacy_contract(tmp_path: Path) -> None:
    """``--json`` payloads keep the legacy key order byte-for-byte."""
    root = crafted_tree(tmp_path)
    run_surface(root, "catalog")

    cases = {
        ("validate",): [
            "skills_root",
            "category",
            "rules_only",
            "issue_count",
            "total_issue_count",
            "issues",
        ],
        ("catalog", "--check"): [
            "skills_root",
            "in_sync",
            "catalog",
            "diff",
        ],
        ("catalog",): [
            "skills_root",
            "catalog",
            "rebuilt",
            "categories",
            "skills",
        ],
        ("discover", "docs"): [
            "skills_root",
            "query",
            "limit",
            "match_count",
            "matches",
        ],
        ("weed",): ["skills_root", "issue_count", "issues"],
        ("repair",): [
            "skills_root",
            "dry_run",
            "planned",
            "plan_count",
            "note",
        ],
        ("move", "drafts/doc-drafts", "notes"): [
            "skills_root",
            "dry_run",
            "skill",
            "from",
            "to",
            "note",
        ],
        ("archive", "drafts/doc-drafts"): [
            "skills_root",
            "dry_run",
            "skill",
            "from",
            "to",
            "note",
        ],
        ("new-category", "beta-cat", "Second"): [
            "skills_root",
            "dry_run",
            "category",
            "description",
            "would_write_description",
            "note",
        ],
        ("merge-plan", "drafts/doc-drafts", "notes/note-taker"): [
            "skills_root",
            "survivor",
            "absorbed",
            "survival_reason",
            "moves",
            "rewrites",
            "category_after",
            "empty_category_after",
        ],
    }

    for args, keys in cases.items():
        code, out, err = run_surface(root, *args, "--json")
        assert code in (0, 1, 3), f"{args}: exit {code}: {err}"
        payload = json.loads(out)
        assert list(payload) == keys, f"{args}: {list(payload)}"


def test_catalog_check_drift_exits_3_and_prints_the_summary(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    code, out, _ = run_surface(root, "catalog", "--check")
    assert code == 3
    assert "Catalog missing" in out


def test_catalog_check_in_sync_exits_0(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    run_surface(root, "catalog")
    code, out, _ = run_surface(root, "catalog", "--check")
    assert code == 0
    assert out.startswith("Catalog in sync:")


def test_mutating_commands_default_to_dry_run(tmp_path: Path) -> None:
    """S2/R6: no ``--apply`` means no write, for every mutating verb."""
    root = crafted_tree(tmp_path)
    run_surface(root, "catalog")
    before = (root / "drafts" / "DESCRIPTION.md").read_text(encoding="utf-8")

    for args in (
        ("repair",),
        ("move", "drafts/doc-drafts", "notes"),
        ("archive", "drafts/doc-drafts"),
        ("new-category", "beta-cat", "Second category"),
    ):
        code, out, _ = run_surface(root, *args)
        assert code == 0, args
        assert "dry-run" in out, args

    assert not (root / "beta-cat").exists()
    assert not (root / "_archive").exists()
    assert (root / "drafts" / "doc-drafts").exists()
    assert (root / "drafts" / "DESCRIPTION.md").read_text(encoding="utf-8") == before


def test_apply_writes_and_rebuilds_the_catalog(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    code, out, _ = run_surface(
        root, "new-category", "beta-cat", "Second category", "--apply"
    )
    assert code == 0
    assert "Wrote beta-cat/DESCRIPTION.md" in out
    assert "Rebuilt" in out
    assert (root / "beta-cat" / "DESCRIPTION.md").exists()


def test_usage_errors_print_the_legacy_error_line(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    code, _out, err = run_surface(root, "move", "nonexistent-skill", "notes")
    assert code == 2
    assert err == (
        "ERROR: Could not find skill directory with SKILL.md: nonexistent-skill\n"
    )


def test_discover_empty_query_is_a_usage_error(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    code, _out, err = run_surface(root, "discover", "")
    assert code == 2
    assert err == "ERROR: Query is empty\n"


def test_validate_full_listing_matches_the_legacy_shape(tmp_path: Path) -> None:
    """The per-issue listing keeps the ``- [type] locator: message`` lines."""
    root = crafted_tree(tmp_path)
    code, out, _ = run_surface(root, "validate")
    assert code == 1
    assert out == (
        "1 validation issue(s) found:\n"
        "- [name-mismatch] drafts/doc-drafts: "
        "Frontmatter name 'wrong-name' does not match directory 'doc-drafts'.\n"
    )


def test_discover_no_match_prints_the_legacy_line(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    run_surface(root, "catalog")
    code, out, _ = run_surface(root, "discover", "no-such-skill-zzz")
    assert code == 0
    assert out == "No matching skills found in CATALOG.md.\n"


def test_repair_apply_reports_applied_steps(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    run_surface(root, "catalog")
    code, out, _ = run_surface(root, "repair", "--apply")
    assert code == 0
    assert "Repairs applied:" in out
    assert "Rebuilt" in out


def test_merge_plan_json_keeps_the_legacy_key_order(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    code, out, _ = run_surface(
        root, "merge-plan", "drafts/doc-drafts", "notes/note-taker", "--json"
    )
    assert code == 0
    payload = json.loads(out)
    assert payload["moves"] == []
    assert payload["category_after"] == "notes"
    assert payload["empty_category_after"] == "drafts"


def test_list_and_show_keep_their_output_shape(tmp_path: Path) -> None:
    """The read-only surface is byte-stable (only ``--skills-root`` is new)."""
    root = clean_tree(tmp_path)

    code, out, _ = run_surface(root, "list")
    assert code == 0
    assert "SKILL" in out
    assert "1 skills in the pack." in out

    code, out, _ = run_surface(root, "show", "alpha")
    assert code == 0
    assert out.startswith("---\nname: alpha")

    code, out, _ = run_surface(root, "show", "nope")
    assert code == 1
