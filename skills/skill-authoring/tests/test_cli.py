"""Tests for the PR-4 CLI contract (design doc §6.1, §5.5).

Covers what the refactor promised:
- the canonical form runs from the repo root (path-based invocation,
  since the pack directory contains a hyphen and is not a ``python3 -m``
  target);
- the back-compat shim (``skill-librarian/scripts/librarian.py``) prints
  the same stdout as the canonical path for every read-only subcommand;
- the exit-code contract: 0 clean, 1 issues found, 2 usage error,
  3 catalog drift (``catalog --check`` only);
- the safety model (§5.5): mutating subcommands default to dry-run and
  touch nothing without ``--apply``;
- ``--json`` emits a stable schema, and ``validate --category`` /
  ``--rules-only`` narrow the report without changing what is found.

Subprocess-based by design: the contract is about how the scripts behave
when invoked by path from the repo root, which is not observable in-process.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parent.parent


def _find_repo_root() -> Path:
    """Walk up from PACK_ROOT to the directory that carries ``.git``.

    A git worktree stores its ``.git`` as a file (pointing at
    ``gitdir``), so the marker is present both in the main clone and in
    any worktree — regardless of how many directory levels deep the
    checkout lives.
    """
    for candidate in PACK_ROOT.parents:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(
        f"no .git marker found walking up from {PACK_ROOT} — "
        "test must run inside a git clone or worktree"
    )


REPO_ROOT = _find_repo_root()
SKILLS_ROOT = REPO_ROOT / "skills"
CLI = PACK_ROOT / "scripts" / "cli.py"
SHIM = PACK_ROOT / "skill-librarian" / "scripts" / "librarian.py"
FIXTURES = PACK_ROOT / "tests" / "fixtures"

READ_ONLY_SUBCOMMANDS = [
    ["validate"],
    ["weed"],
    ["discover", "pdf"],
    ["rules"],
]


def run(*args: str, cwd: Path | None = None, env_root: Path | None = None) -> tuple[int, str, str]:
    """Invoke the canonical CLI by path; returns (exit, stdout, stderr)."""
    command = [sys.executable, str(CLI), *args]
    if env_root is not None:
        command += ["--skills-root", str(env_root)]
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def run_shim(*args: str) -> tuple[int, str, str]:
    """Invoke the old path — the back-compat shim."""
    completed = subprocess.run(
        [sys.executable, str(SHIM), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def test_canonical_form_runs_from_repo_root():
    """§6.1: ``python3 skills/skill-authoring/scripts/cli.py validate`` with
    cwd = the repo root works and reports the library's issues."""
    exit_code, stdout, stderr = run("validate", cwd=REPO_ROOT)

    assert exit_code == 1, f"expected exit 1 (issues found), got {exit_code}: {stderr}"
    assert stdout.startswith("14 validation issue(s) found:\n"), stdout[:100]
    assert stderr == ""


def test_shim_matches_canonical_for_every_read_only_subcommand():
    """The old path and the canonical path print identical stdout."""
    for subcommand in READ_ONLY_SUBCOMMANDS:
        canonical = run(*subcommand)
        shim = run_shim(*subcommand)

        assert canonical[0] == shim[0], f"{subcommand}: exit {canonical[0]} vs {shim[0]}"
        assert canonical[1] == shim[1], (
            f"{subcommand}: shim stdout drifted from canonical\n"
            f"--- canonical\n{canonical[1]}\n--- shim\n{shim[1]}"
        )


def test_shim_runs_from_a_clean_interpreter():
    """The back-compat path works from a clean interpreter: the shim's
    ``sys.path`` prepend of the pack's ``scripts/`` directory is what lets
    ``from cli import main`` resolve without any packaging (NG5), and the
    exit code follows the canonical CLI's contract (1: issues found)."""
    exit_code, stdout, _stderr = run_shim("validate")
    assert exit_code == 1, f"expected exit 1 (issues found), got {exit_code}"
    assert stdout.startswith("14 validation issue(s) found:\n"), stdout[:100]


def test_validate_report_is_the_committed_baseline():
    """The 14 issues / 15 lines the tree reports today hold through the
    canonical path (hard constraint: read-only stdout is unchanged)."""
    exit_code, stdout, _ = run("validate")

    lines = stdout.splitlines()
    assert exit_code == 1
    assert len(lines) == 15, f"expected 15 output lines, got {len(lines)}"
    assert lines[0] == "14 validation issue(s) found:"
    assert sum(1 for line in lines if line.startswith("- [")) == 14


def test_exit_code_0_clean_on_crafted_tree():
    """Exit 0: a valid crafted tree reports no issues."""
    exit_code, stdout, _ = run("validate", env_root=FIXTURES / "clean")
    assert exit_code == 0, f"expected 0, got {exit_code}"
    assert stdout.strip() == "No validation issues found."


def test_exit_code_1_issues_found_on_missing_description():
    """Exit 1: the validator reports exactly the crafted issue."""
    exit_code, stdout, _ = run("validate", env_root=FIXTURES / "missing-description")
    assert exit_code == 1
    assert stdout.startswith("1 validation issue(s) found:")


def test_exit_code_1_weed_reports_issues():
    """Exit 1: ``weed`` exits nonzero when it finds weeds (the library's
    ``shared`` category is the standing example)."""
    exit_code, stdout, _ = run("weed")
    assert exit_code == 1
    assert "empty-category" in stdout


def test_exit_code_2_usage_error_unknown_flag():
    """Exit 2: argparse rejects an unrecognized flag."""
    exit_code, _, stderr = run("validate", "--nope")
    assert exit_code == 2
    assert "unrecognized arguments" in stderr


def test_exit_code_2_usage_error_missing_argument():
    """Exit 2: a required argument is absent."""
    exit_code, _, stderr = run("discover")
    assert exit_code == 2
    assert "the following arguments are required" in stderr


def test_exit_code_2_nonexistent_skill_is_a_usage_error():
    """A nonexistent skill argument is caller-input, not a found issue:
    exit 2 (contract-faithful reading of §6.1; documented in the summary).

    The legacy ``ERROR: …`` stderr line is preserved.
    """
    exit_code, _, stderr = run("move", "nonexistent-skill", "automation")
    assert exit_code == 2
    assert "ERROR: Could not find skill directory with SKILL.md: nonexistent-skill" in stderr


def test_catalog_check_drifts_to_3_on_an_empty_root(tmp_path: Path):
    """A skills root with no skills drifts: the tracked catalog is missing.
    So there is nothing to be in sync with (exit 3, not a usage error)."""
    root = tmp_path / "skills"
    (root / "empty-cat").mkdir(parents=True)

    exit_code, stdout, _ = run("catalog", "--check", env_root=root)

    assert exit_code == 3, f"expected exit 3 (missing catalog = drift), got {exit_code}"
    assert "Catalog missing" in stdout


def test_mutating_commands_default_to_dry_run(tmp_path: Path):
    """§5.5: with no ``--apply``, mutating commands change nothing on disk."""
    root = _crafted_tree(tmp_path)
    run("catalog", env_root=root)
    draft_desc_before = (root / "drafts" / "DESCRIPTION.md").read_text()

    for subcommand in (["repair"], ["new-category", "beta-cat", "Second category"]):
        exit_code, stdout, _ = run(*subcommand, env_root=root)

        assert exit_code == 0, f"{subcommand}: dry-run exited {exit_code}"
        assert "dry-run" in stdout, f"{subcommand}: output must say it is a preview"
        assert not (root / "beta-cat").exists(), "new-category created a directory in dry-run"
        assert (root / "drafts" / "DESCRIPTION.md").read_text() == draft_desc_before, (
            "repair rewrote a file in dry-run"
        )
    assert not (root / "_archive").exists()


def test_dry_run_leaves_a_clean_worktree():
    """Hard constraint: the repo tree is untouched by a no-flag mutating run."""
    before = _git_status()

    run("repair")
    run("new-category", "zz-dry-run-only", "Never created")
    run("move", "web/xurl", "automation")
    run("archive", "web/xurl")

    assert _git_status() == before, "a dry-run command modified the worktree"


def test_apply_then_revert_round_trip(tmp_path: Path):
    """``--apply`` does the work dry-run described, on a crafted tree."""
    root = _crafted_tree(tmp_path)
    run("catalog", env_root=root)

    exit_code, stdout, _ = run("new-category", "beta-cat", "Second category", "--apply", env_root=root)

    assert exit_code == 0
    assert (root / "beta-cat" / "DESCRIPTION.md").exists()
    assert "Second category" in (root / "beta-cat" / "DESCRIPTION.md").read_text()
    assert "dry-run" not in stdout


def test_skills_root_flag_overrides_path_derivation(tmp_path: Path):
    """``--skills-root`` wins over the layout-derived root (explicit beats
    derived — the tests and CI use it to point at crafted trees)."""
    root = _crafted_tree(tmp_path)

    _, stdout, _ = run("validate", env_root=root)

    assert str(root) in stdout or "1 validation issue(s) found:" in stdout
    assert (root / "CATALOG.md").exists() is False  # validate does not write


def test_json_schema_is_stable_per_subcommand(tmp_path: Path):
    """Every subcommand's ``--json`` parses and carries its documented keys."""
    root = _crafted_tree(tmp_path)
    run("catalog", env_root=root)

    cases: list[tuple[list[str], list[str]]] = [
        (["validate"], ["skills_root", "issue_count", "issues"]),
        (["validate", "--category", "drafts"], ["category", "rules_only", "total_issue_count"]),
        (["validate", "--rules-only"], ["rules_only"]),
        (["catalog", "--check"], ["in_sync", "catalog", "diff"]),
        (["discover", "docs"], ["query", "limit", "match_count", "matches"]),
        (["weed"], ["issue_count", "issues"]),
        (["repair"], ["dry_run", "planned"]),
        (["move", "drafts/doc-drafts", "notes"], ["dry_run", "from", "to"]),
        (["archive", "drafts/doc-drafts"], ["dry_run", "from", "to"]),
        (["new-category", "beta-cat", "Second"], ["dry_run", "category", "description"]),
        (["merge-plan", "drafts/doc-drafts", "notes/note-taker"], ["survivor", "absorbed", "moves", "rewrites"]),
    ]

    for subcommand, keys in cases:
        exit_code, stdout, stderr = run(*subcommand, "--json", env_root=root)

        assert exit_code in (0, 1, 3), f"{subcommand}: exit {exit_code}: {stderr}"
        payload = json.loads(stdout)
        assert isinstance(payload, dict), f"{subcommand}: payload is not an object"
        for key in keys:
            assert key in payload, f"{subcommand}: JSON missing key {key!r}"
        if subcommand[:1] == ["validate"]:
            assert payload["skills_root"] == str(root)


def test_validate_category_and_rules_only_narrow_without_hiding():
    """The flags filter the report, not the discovery: the count line still
    states the unfiltered total and the exit code still tracks it."""
    exit_code, stdout, _ = run("validate", "--category", "drafts-not-a-category")
    assert exit_code == 1
    assert "0 in scope" in stdout

    _, scoped, _ = run("validate", "--rules-only")
    assert "13 in scope" in scoped
    # The scoped version includes a note after the total count, but the test
    # should assert that the line starts with the total count, not that it ends
    # with the scoped note.
    assert scoped.startswith("14 validation issue(s) found (13 in scope rules-only):")

    _, full, _ = run("validate")
    assert full.splitlines()[0] == "14 validation issue(s) found:"
    assert full.count("\n- [") == 14


def test_merge_plan_is_read_only():
    """``merge-plan`` emits the plan; it never executes anything."""
    before = _git_status()

    exit_code, stdout, _ = run("merge-plan", "automation/qwen-web", "automation/qwen-web-arwaky-dev")

    assert exit_code == 0
    assert stdout.startswith("# Merge plan\n")
    assert "Survivor:" in stdout
    assert "Absorbed:" in stdout
    assert "## Moves" in stdout
    assert "## Rewrite" in stdout
    assert "## Delete" in stdout
    assert _git_status() == before


def test_merge_plan_rejects_a_bare_skill_reference():
    """A bare name is ambiguous in a merge (which category?); usage error."""
    exit_code, _, stderr = run("merge-plan", "qwen-web", "xurl")
    assert exit_code == 2
    assert "must be 'category/skill'" in stderr


def test_rules_markdown_round_trip_unchanged():
    """PR-3's gate still holds: the SSOT doc regenerates byte-for-byte."""
    from skill_rules import RULES  # noqa: F401  (asserts the SSOT imports)

    committed = PACK_ROOT / "_rules" / "skill-rules.md"
    exit_code, stdout, _ = run("rules", "--markdown")

    assert exit_code == 0
    assert stdout == committed.read_text(encoding="utf-8")


def test_catalog_artifact_is_unchanged_by_the_refactor():
    """The catalog the refactor leaves behind is the tracked one: the
    placeholder row for the asset container survives, untouched."""
    catalog_md = REPO_ROOT / "skills" / "CATALOG.md"
    text = catalog_md.read_text(encoding="utf-8")
    assert text.startswith("# Skills Catalog\n")
    assert "| shared | (missing DESCRIPTION.md) | 0 |" in text
    assert "skill-librarian | skill-authoring |" in text


def test_pack_is_not_importable_as_a_dotted_package():
    """The pack path contains a hyphen, so ``python3 -m`` cannot target it
    (design §6.1): importing the dotted form fails before any code runs."""
    completed = subprocess.run(
        [sys.executable, "-m", "skills.skill-authoring.scripts.cli", "validate"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode != 0
    assert "No module named" in completed.stderr


def test_can_be_imported_by_path_without_side_effects(tmp_path: Path):
    """Importing the package does not write anything to the caller's tree."""
    marker = tmp_path / "untouched"
    marker.mkdir()
    completed = subprocess.run(
        [sys.executable, "-c",
         ("import sys; sys.path.insert(0, 'skills/skill-authoring/scripts'); "
          "import catalog, discover, mergeplan, model, mutate; "
          f"import os; print(sorted(os.listdir({str(marker)!r})))")],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, f"stderr: {completed.stderr}"
    assert completed.stdout.strip() == "[]"


def test_weed_exits_0_on_a_clean_tree():
    """The other half of the weed contract: no weeds means exit 0."""
    exit_code, stdout, _ = run("weed", env_root=FIXTURES / "clean")
    assert exit_code == 0
    assert stdout == "Weeding report:\nNo obvious weeds found.\n"


def test_discover_limit_caps_results(tmp_path: Path):
    """``--limit`` caps the result count."""
    root = _crafted_tree(tmp_path)
    run("catalog", env_root=root)

    # "notes" matches both rows (category + path hit); the cap keeps one.
    _, stdout, _ = run("discover", "notes", "--limit", "1", env_root=root)
    rows = [
        line
        for line in stdout.splitlines()
        if line.startswith("| ")
        and "---|" not in line
        and line != "| Skill | Category | Description | Path | Score |"
    ]
    assert len(rows) == 1


def test_discover_reads_the_catalog(tmp_path: Path):
    """Discovery answers from CATALOG.md: a row only the catalog holds is
    found, and the empty-query error is a usage error (exit 2)."""
    root = _crafted_tree(tmp_path)
    run("catalog", env_root=root)

    exit_code, stdout, _ = run("discover", "docs", env_root=root)
    assert exit_code == 0
    assert "| doc-drafts |" in stdout

    exit_code, _, stderr = run("discover", "", env_root=root)
    assert exit_code == 2
    assert "ERROR: Query is empty" in stderr


def test_discover_limit_caps_results_is_empty_without_matches(tmp_path: Path):
    """No match prints the legacy single line and exits 0."""
    exit_code, stdout, _ = run("discover", "definitely-not-a-real-skill-term")
    assert exit_code == 0
    assert stdout.strip() == "No matching skills found in CATALOG.md."


def test_merge_plan_chooses_the_non_stale_name(tmp_path: Path):
    """Rule from prune-skills §Merge Rules: the skill whose frontmatter
    ``name:`` matches its folder survives; a name-mismatch is stale."""
    root = tmp_path / "skills"
    (root / "cat").mkdir(parents=True)
    (root / "cat" / "DESCRIPTION.md").write_text("---\ndescription: Cat\n---\n", encoding="utf-8")
    (root / "cat" / "stale-name").mkdir()
    (root / "cat" / "stale-name" / "SKILL.md").write_text(
        "---\nname: something-else\ndescription: Same job.\n---\n\n# stale-name\n", encoding="utf-8"
    )
    (root / "cat" / "aligned-name").mkdir()
    (root / "cat" / "aligned-name" / "SKILL.md").write_text(
        "---\nname: aligned-name\ndescription: Same job.\n---\n\n# aligned-name\n", encoding="utf-8"
    )

    exit_code, stdout, _ = run("merge-plan", "cat/stale-name", "cat/aligned-name", env_root=root)

    assert exit_code == 0
    assert "- Survivor: `cat/aligned-name`" in stdout
    assert "- Absorbed: `cat/stale-name`" in stdout
    assert "name-mismatch" in stdout


def test_archive_dry_run_renames_nothing(tmp_path: Path):
    """Archive dry-run describes the rename it would do without doing it."""
    root = _crafted_tree(tmp_path)
    run("catalog", env_root=root)

    exit_code, stdout, _ = run("archive", "drafts/doc-drafts", env_root=root)

    assert exit_code == 0
    assert "SKILL.md -> SKILL.md.archived" in stdout
    assert (root / "drafts" / "doc-drafts" / "SKILL.md").exists()
    assert not (root / "_archive").exists()


def test_catalog_check_drift_count_matches_diff(tmp_path: Path):
    """The drift message's diff-line count is the actual diff size."""
    root = _crafted_tree(tmp_path)
    run("catalog", env_root=root)
    (root / "drafts" / "doc-drafts" / "SKILL.md").write_text(
        "---\nname: doc-drafts\ndescription: Changed description.\n---\n\n# doc-drafts\n",
        encoding="utf-8",
    )

    exit_code, stdout, _ = run("catalog", "--check", env_root=root)
    assert exit_code == 3
    assert "diff line(s)" in stdout


def test_validate_category_scope_counts_are_honest():
    """The scoped count is a subset of the total; the total never drops."""
    _, stdout, _ = run("validate", "--category", "code-quality")
    first = stdout.splitlines()[0]
    assert "14 validation issue(s) found (3 in scope" in first

    _, stdout, _ = run("validate", "--category", "research")
    assert "1 in scope" in stdout


def test_move_dry_run_does_not_move(tmp_path: Path):
    """Move dry-run leaves both folders exactly where they were."""
    root = _crafted_tree(tmp_path)
    run("catalog", env_root=root)

    exit_code, stdout, _ = run("move", "drafts/doc-drafts", "notes", env_root=root)

    assert exit_code == 0
    assert "drafts/doc-drafts -> notes/doc-drafts" in stdout
    assert (root / "drafts" / "doc-drafts" / "SKILL.md").exists()
    assert not (root / "notes" / "doc-drafts").exists()


def test_skills_root_with_tilde_is_not_supported():
    """``--skills-root`` resolves the path the caller gives; a nonexistent
    root is a usage error with the legacy ERROR line."""
    exit_code, _, stderr = run("validate", "--skills-root", "/definitely/not/here")
    assert exit_code == 2
    assert "ERROR: Skills root does not exist" in stderr


def test_weed_json_reports_the_same_weeds_as_text():
    """The JSON and text forms report the same weed set."""
    _, text_out, _ = run("weed")
    _, json_out, _ = run("weed", "--json")

    payload = json.loads(json_out)
    assert payload["issue_count"] == 2
    assert {issue["type"] for issue in payload["issues"]} == {
        "empty-category",
        "missing-category-description",
    }
    assert "empty-category: shared" in text_out


def test_catalog_does_not_drift_the_committed_artifact_in_check_mode():
    """``catalog --check`` regenerates to a temp file — the tracked catalog
    is never the file it writes, whether or not it is currently in sync."""
    before = _git_status()
    exit_code, _, _ = run("catalog", "--check")
    # 0 = in sync, 3 = drift; --check must report, never write.
    assert exit_code in (0, 3)
    assert _git_status() == before


def test_crafted_description_with_literal_entity_fails_the_gate(tmp_path: Path):
    """The escaping round-trip assertion (§9.2): a crafted description that
    carries the literal text ``&#124;`` does not survive the escape→unescape
    round-trip, so ``catalog --check`` fails it as drift (exit 3) rather than
    letting the index silently corrupt.

    The drift must be the cell round-trip, not a content diff: the cell's
    rendered row is what the tree renders, so the diff against the tracked
    catalog is empty and only the cell assertion flags it.
    """
    root = tmp_path / "skills"
    (root / "cat").mkdir(parents=True)
    (root / "cat" / "DESCRIPTION.md").write_text(
        "---\ndescription: Crafted cells\n---\n", encoding="utf-8"
    )
    (root / "cat" / "corrupt").mkdir()
    (root / "cat" / "corrupt" / "SKILL.md").write_text(
        "---\nname: corrupt\ndescription: bad cell &#124; here\n---\n\n# corrupt\n",
        encoding="utf-8",
    )

    from catalog import catalog_cell_problems, rebuild_catalog

    entries, categories = rebuild_catalog(root)
    problems = catalog_cell_problems(entries, categories)
    assert problems, "the crafted &#124; cell must fail the round-trip"
    assert any("corrupt" in p for p in problems)

    # The cell round-trips lossily: md_escape leaves the literal entity alone
    # and the parser unescapes it to a pipe.
    from skill_rules import md_escape

    lossy = "bad cell &#124; here"
    assert md_escape(lossy).replace("&#124;", "|") != lossy

    # A real pipe round-trips: escape writes &#124;, the parser reads | back,
    # so a legitimate cell is never flagged.
    from skill_rules import md_unescape

    assert md_unescape(md_escape("a|b")) == "a|b"

    # Line-break characters beyond \n survive md_escape but the reader's
    # splitlines() chops the row at them — fail closed (review bug fix).
    from catalog import _cell_round_trips

    assert not _cell_round_trips("bad\rcell")
    assert not _cell_round_trips("bad\x85cell")
    assert _cell_round_trips("a|b")


def test_check_catalog_reports_cell_drift_not_just_content_diff(tmp_path: Path):
    """``check_catalog`` is fail-closed on cells: when a rendered cell does
    not round-trip through the escape→unescape path, the check reports the
    cell drift even when the content diff is empty.

    The diff-based branch is the ordinary "artifact is stale" case. The cell
    assertion is the §9.2 guard: a tracked artifact that matches what the tree
    renders byte-for-byte but carries a lossy cell is still drift, and only
    the cell check can see it.
    """
    root = tmp_path / "skills"
    (root / "cat").mkdir(parents=True)
    (root / "cat" / "DESCRIPTION.md").write_text(
        "---\ndescription: Crafted cells\n---\n", encoding="utf-8"
    )
    (root / "cat" / "corrupt").mkdir()
    (root / "cat" / "corrupt" / "SKILL.md").write_text(
        "---\nname: corrupt\ndescription: bad cell &#124; here\n---\n\n# corrupt\n",
        encoding="utf-8",
    )

    import catalog

    # The artifact the tree renders (diff is empty here) carries the
    # lossy cell; check_catalog must flag it via the cell assertion, not
    # the diff.
    catalog.rebuild_catalog(root)

    in_sync, summary, diff_lines = catalog.check_catalog(root)
    assert not in_sync
    # The cell round-trips lossily: md_escape leaves the literal &#124; alone,
    # the parser unescapes it to a pipe, so the artifact lies about the tree.
    assert "do not round-trip" in summary, f"expected the cell drift, got: {summary}"
    assert diff_lines, "the cell drift must be surfaced as diff-like lines"


def _crafted_tree(tmp_path: Path) -> Path:
    """A small, deterministic skills root with one known validation issue."""
    root = tmp_path / "skills"
    (root / "drafts").mkdir(parents=True)
    (root / "notes").mkdir()

    (root / "drafts" / "DESCRIPTION.md").write_text(
        "---\ndescription: Draft skills\n---\n", encoding="utf-8"
    )
    (root / "notes" / "DESCRIPTION.md").write_text(
        "---\ndescription: Note skills\n---\n", encoding="utf-8"
    )

    # A name-mismatch issue: the frontmatter name is not the folder name.
    (root / "drafts" / "doc-drafts").mkdir()
    (root / "drafts" / "doc-drafts" / "SKILL.md").write_text(
        "---\nname: wrong-name\ndescription: Drafts docs.\n---\n\n# doc-drafts\n",
        encoding="utf-8",
    )

    (root / "notes" / "note-taker").mkdir()
    (root / "notes" / "note-taker" / "SKILL.md").write_text(
        "---\nname: note-taker\ndescription: Takes notes.\n---\n\n# note-taker\n",
        encoding="utf-8",
    )

    return root


def _git_status() -> str:
    """The worktree's short status — a before/after equality oracle."""
    completed = subprocess.run(
        ["git", "status", "--short"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout


def test_shutil_available():
    """The mutations import shutil; assert the module loads at all."""
    import catalog
    import mutate

    assert callable(mutate.fail)
    assert callable(catalog.rebuild_catalog)
    assert shutil.move is not None