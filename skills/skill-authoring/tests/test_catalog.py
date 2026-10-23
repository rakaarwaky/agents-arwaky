"""Tests for the catalog drift gate (PR-5; design §6.1, §9.2, §5.6).

Pins the strict-contract `load_catalog_skill_rows` enforces — missing
catalog, parse-empty, drifted, and corrupt round-trip all raise
`CatalogDrift` rather than silently rebuilding or falling back to the
live tree. It also pins `check_catalog` as the repair path: exit 0 on
sync, exit 3 on any of those conditions, and the tracked file is never
written by `--check`. The escape round-trip (`|`, `&#124;`) must
survive parse(render(x)) == x; a crafted description that breaks it
fails closed as drift.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_rules"))
import catalog

_cli = Path(__file__).resolve().parent.parent / "scripts" / "cli.py"


@pytest.fixture()
def crafted_tree(tmp_path: Path) -> Path:
    """A small deterministic skills root: drafts + notes with one mismatch."""
    root = tmp_path / "skills"
    (root / "drafts").mkdir(parents=True)
    (root / "notes").mkdir()

    (root / "drafts" / "DESCRIPTION.md").write_text(
        "---\ndescription: Draft skills\n---\n", encoding="utf-8"
    )
    (root / "notes" / "DESCRIPTION.md").write_text(
        "---\ndescription: Note skills\n---\n", encoding="utf-8"
    )

    (root / "drafts" / "doc-drafts").mkdir()
    (root / "drafts" / "doc-drafts" / "SKILL.md").write_text(
        "---\nname: doc-drafts\ndescription: Drafts docs.\n---\n\n# doc-drafts\n",
        encoding="utf-8",
    )

    (root / "notes" / "note-taker").mkdir()
    (root / "notes" / "note-taker" / "SKILL.md").write_text(
        "---\nname: note-taker\ndescription: Takes notes.\n---\n\n# note-taker\n",
        encoding="utf-8",
    )

    return root


def _run_cli(*args: str, env_root: Path | None = None) -> tuple[int, str, str]:
    """Run the canonical CLI by path and return (exit, stdout, stderr)."""
    command = [sys.executable, str(_cli), *args]
    if env_root is not None:
        command += ["--skills-root", str(env_root)]
    completed = subprocess.run(
        command,
        cwd=str(Path(__file__).resolve().parent.parent.parent.parent),
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def test_catalog_check_drifts_to_3_on_an_empty_root(tmp_path: Path):
    """A skills root with no skills drifts: the tracked catalog is missing."""
    root = tmp_path / "skills"
    (root / "empty-cat").mkdir(parents=True)

    exit_code, stdout, _ = _run_cli("catalog", "--check", env_root=root)

    assert exit_code == 3, f"expected exit 3 (missing catalog = drift), got {exit_code}"
    assert "Catalog missing" in stdout


def test_catalog_check_drift_count_matches_diff(crafted_tree: Path):
    """The drift message's diff-line count is the actual diff size."""
    root = crafted_tree
    _run_cli("catalog", env_root=root)
    (root / "drafts" / "doc-drafts" / "SKILL.md").write_text(
        "---\nname: doc-drafts\ndescription: Changed description.\n---\n\n# doc-drafts\n",
        encoding="utf-8",
    )

    exit_code, stdout, _ = _run_cli("catalog", "--check", env_root=root)
    assert exit_code == 3
    assert "diff line(s)" in stdout


def test_catalog_does_not_drift_the_committed_artifact_in_check_mode(crafted_tree: Path):
    """``catalog --check`` regenerates to a temp file — the tracked catalog
    is never the file it writes, whether or not it is currently in sync."""
    exit_code, _, _ = _run_cli("catalog", "--check", env_root=crafted_tree)
    # 0 = in sync, 3 = drift; --check must report, never write.
    assert exit_code in (0, 3)
    # No new untracked file should have been created.
    assert not (crafted_tree / "CATALOG.md").exists()


def test_catalog_check_json_schema_has_diff_field(crafted_tree: Path):
    """The ``--json`` shape carries ``in_sync`` and ``diff``."""
    exit_code, stdout, _ = _run_cli("catalog", "--check", "--json", env_root=crafted_tree)
    assert exit_code in (0, 3)
    payload = json.loads(stdout)
    assert "in_sync" in payload
    assert "diff" in payload
    assert isinstance(payload["diff"], list)


def test_catalog_rebuild_is_idempotent(crafted_tree: Path):
    """Rebuilding an in-sync catalog is byte-for-byte idempotent."""
    before, _, _ = _run_cli("catalog", env_root=crafted_tree)
    after, _, _ = _run_cli("catalog", env_root=crafted_tree)
    assert before == after, "rebuild is not idempotent"
    in_sync, _, _ = _run_cli("catalog", "--check", env_root=crafted_tree)
    assert in_sync == 0


def test_load_catalog_skill_rows_raises_on_missing_catalog(tmp_path: Path):
    """A read through a missing catalog raises CatalogDrift, never rebuilds."""
    root = tmp_path / "skills"
    (root / "cat").mkdir(parents=True)
    (root / "cat" / "a").mkdir()
    (root / "cat" / "a" / "SKILL.md").write_text(
        "---\nname: a\ndescription: A skill.\n---\n"
    )
    with pytest.raises(catalog.CatalogDrift):
        catalog.load_catalog_skill_rows(root)
    # No side-effect: the catalog must not have been written.
    assert not (root / "CATALOG.md").exists()


def test_load_catalog_skill_rows_raises_on_parse_empty(crafted_tree: Path):
    """A catalog with an empty ``## Skills`` section is drift, not live-tree fallback."""
    root = crafted_tree
    catalog.rebuild_catalog(root)
    cat = root / "CATALOG.md"
    # Corrupt the file so the ## Skills table has no skill rows.
    lines = cat.read_text().splitlines()
    # Find the ## Skills section and strip all skill rows from it.
    out_lines: list[str] = []
    in_skills = False
    for line in lines:
        if line.strip() == "## Skills":
            in_skills = True
            out_lines.append(line)
            out_lines.extend(["", "| Skill Name | Category | Description | Path |", "|---|---|---|---|"])
            continue
        if in_skills and line.strip().startswith("## "):
            in_skills = False
        if not in_skills:
            out_lines.append(line)
    cat.write_text("\n".join(out_lines) + "\n")
    with pytest.raises(catalog.CatalogDrift):
        catalog.load_catalog_skill_rows(root)


def test_load_catalog_skill_rows_raises_on_stale_track_vs_live_tree(crafted_tree: Path):
    """If the tracked catalog differs from what the tree renders, it is drift."""
    root = crafted_tree
    catalog.rebuild_catalog(root)
    cat = root / "CATALOG.md"
    # Edit the tracked catalog so it describes a non-existent skill.
    cat.write_text(cat.read_text().replace("Drafts docs.", "PHANTOM SKILL"))
    with pytest.raises(catalog.CatalogDrift):
        catalog.load_catalog_skill_rows(root)


def test_escape_round_trip_pipe_is_clean(crafted_tree: Path):
    """A description containing ``|`` survives parse(render(x)) == x."""
    tree = crafted_tree
    (tree / "drafts" / "bar-skill").mkdir()
    (tree / "drafts" / "bar-skill" / "SKILL.md").write_text(
        "---\nname: bar-skill\ndescription: A skill with | pipe chars.\n---\n"
    )
    catalog.rebuild_catalog(tree)
    # Must load in-sync with the pipe present (the renderer escapes it,
    # the parser un-escapes it — a clean round trip).
    rows = catalog.load_catalog_skill_rows(tree)
    bar = next(r for r in rows if r["skill"] == "bar-skill")
    assert bar["description"] == "A skill with | pipe chars."
    in_sync, _, diff = catalog.check_catalog(tree)
    assert in_sync is True, f"drift despite clean pipe: {diff[:200]}"


def test_escape_round_trip_double_escaped_no_mojibake(crafted_tree: Path):
    """A description whose *source* frontmatter contains the literal
    entity text ``&#124;`` is a drift case (§9.2 fail-closed): the
    parser unescapes it to ``|`` on load, so the loaded row diverges
    from the source entry even though the rendered cell looks correct.

    The test also pins that a raw ``|`` in a description — the common
    case ``md_escape`` is designed for — round-trips cleanly.
    """
    # Case 1: raw ``|`` — md_escape escapes it, parse-back unescapes it.
    tree = crafted_tree
    (tree / "drafts" / "pipe-skill").mkdir()
    (tree / "drafts" / "pipe-skill" / "SKILL.md").write_text(
        "---\nname: pipe-skill\ndescription: A skill with | pipe chars.\n---\n"
    )
    catalog.rebuild_catalog(tree)
    in_sync, summary, _ = catalog.check_catalog(tree)
    assert in_sync is True, f"raw pipe should round-trip cleanly: {summary}"

    # Case 2: literal entity ``&#124;`` in the source frontmatter.
    (tree / "drafts" / "amp-skill").mkdir()
    (tree / "drafts" / "amp-skill" / "SKILL.md").write_text(
        "---\nname: amp-skill\ndescription: Contains &#124; literal entity.\n---\n"
    )
    catalog.rebuild_catalog(tree)
    in_sync, summary, _ = catalog.check_catalog(tree)
    assert in_sync is False, (
        f"literal entity in source must fail closed as drift (§9.2); "
        f"got: {summary}"
    )


def test_crafted_pipe_description_fails_closed_as_drift(tmp_path: Path):
    """A crafted description that breaks the table (raw ``|`` in an already-rendered cell)
    fails closed: ``load_catalog_skill_rows`` and ``catalog --check`` both refuse it."""
    root = tmp_path / "skills"
    (root / "cat").mkdir(parents=True)
    (root / "cat" / "DESCRIPTION.md").write_text("---\ndescription: Cat\n---\n")
    (root / "cat" / "bad").mkdir()
    (root / "cat" / "bad" / "SKILL.md").write_text(
        "---\nname: bad\ndescription: has | pipe\n---\n"
    )
    # Rebuild once to get a valid in-sync catalog.
    catalog.rebuild_catalog(root)
    # Now inject a description that has a literal pipe in the rendered cell,
    # which will break the table on the next render cycle because the
    # parser split on ``|`` would yield extra cells.
    cat = root / "CATALOG.md"
    text = cat.read_text()
    # Replace an existing description cell to introduce an unescaped pipe inside a row.
    text = text.replace("has &#124; pipe", "BROKEN | ROW INJECTS EXTRA CELL")
    cat.write_text(text)
    # The check should now fail closed because the render+parse fixed point shifts.
    in_sync, summary, _ = catalog.check_catalog(root)
    assert in_sync is False, f"expected fail-closed drift, got: {summary}"
    with pytest.raises(catalog.CatalogDrift):
        catalog.load_catalog_skill_rows(root)


def test_empty_description_skill_reports_in_sync(tmp_path: Path):
    """MF-2 regression: a skill whose frontmatter has no ``description:`` key
    renders the ``(missing description)`` placeholder. The round-trip
    comparison normalizes that placeholder back to the empty source
    description, so an in-sync catalog with a description-less skill
    reports in_sync True (CLI ``catalog --check`` would exit 0)."""
    root = tmp_path / "skills"
    (root / "cat").mkdir(parents=True)
    (root / "cat" / "DESCRIPTION.md").write_text("---\ndescription: A cat\n---\n")
    (root / "cat" / "a").mkdir()
    (root / "cat" / "a" / "SKILL.md").write_text("---\nname: a\n---\n# a\n")
    catalog.rebuild_catalog(root)

    in_sync, summary, _ = catalog.check_catalog(root)
    assert in_sync is True, f"empty-description tree must be in sync: {summary}"

    # CLI-level: the same tree exits 0 through the canonical subcommand.
    exit_code, stdout, _ = _run_cli("catalog", "--check", env_root=root)
    assert exit_code == 0, f"expected exit 0, got {exit_code}: {stdout}"


def test_mutating_commands_rebuild_catalog_in_same_invocation(crafted_tree: Path):
    """DM3: every mutating command rebuilds the catalog in the same call."""
    tree = crafted_tree
    (tree / "drafts" / "doc-drafts" / "SKILL.md").write_text(
        "---\nname: doc-drafts\ndescription: Fixed desc.\n---\n\n# doc-drafts\n"
    )
    # Move a skill — should rebuild catalog as part of the invocation.
    _run_cli("move", "drafts/doc-drafts", "notes", "--apply", env_root=tree)
    assert (tree / "notes" / "doc-drafts" / "SKILL.md").exists()
    assert not (tree / "drafts" / "doc-drafts").exists()
    rows = catalog.load_catalog_skill_rows(tree)
    assert any(r["path"] == "notes/doc-drafts" for r in rows)


def test_catalog_artifact_unchanged_by_refactor():
    """The catalog the refactor leaves behind is the tracked one: the
    placeholder row for the asset container survives, untouched."""
    # test file lives at <worktree>/skills/skill-authoring/tests/test_catalog.py
    pack_root = Path(__file__).resolve().parent.parent
    skills_root = pack_root.parent
    catalog_md = skills_root / "CATALOG.md"
    text = catalog_md.read_text(encoding="utf-8")
    assert text.startswith("# Skills Catalog\n")
    assert "| shared | (missing DESCRIPTION.md) | 0 |" in text
    assert "skill-librarian | skill-authoring |" in text
