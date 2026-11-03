"""Acceptance tests — map 1:1 to business requirements (FRD/PRD IDs)."""
from __future__ import annotations

from pathlib import Path


def _make_pack(tmp_path: Path) -> Path:
    pack = tmp_path / "skills"
    (pack / "web" / "fetch-mcp").mkdir(parents=True)
    (pack / "web" / "fetch-mcp" / "SKILL.md").write_text(
        "---\nname: fetch-mcp\ndescription: Scrapes web to markdown.\n---\n\n# Fetch\n",
        encoding="utf-8",
    )
    return pack


def test_acceptance_fr_skill_discovery(tmp_path: Path):
    """AC-SKILLS-001: FR-003 — every skill in the pack is discoverable."""
    from modules.skills.src.capabilities_skills_lister import (
    SkillsLister,
)

    rows = list(SkillsLister(_make_pack(tmp_path)).list_skills())
    assert [r.name for r in rows] == ["fetch-mcp"]


def test_acceptance_fr_skill_lookup(tmp_path: Path):
    """AC-SKILLS-002: FR-003 — a discovered skill's content is retrievable."""
    from modules.shared.src.skills.taxonomy_skills_vo import SkillQuery
    from modules.skills.src.capabilities_skills_reader import SkillsPackReader

    pack = _make_pack(tmp_path)
    content = SkillsPackReader(pack).show_skill(SkillQuery("fetch-mcp"))
    assert content is not None
    assert "fetch-mcp" in content
    assert "Scrapes web to markdown" in content


def test_acceptance_fr_skill_unknown(tmp_path: Path):
    """AC-SKILLS-003: FR-003 — an unknown skill name returns None."""
    from modules.shared.src.skills.taxonomy_skills_vo import SkillQuery
    from modules.skills.src.capabilities_skills_reader import SkillsPackReader

    pack = _make_pack(tmp_path)
    content = SkillsPackReader(pack).show_skill(SkillQuery("nope-missing"))
    assert content is None

# ─── Authoring acceptance (one case per `aa skills` subcommand) ────────
def test_acceptance_lint_reports_and_exits(tmp_path: Path):
    """AC-SKILLS-010: ``lint`` reports the crafted issue with exit 1."""
    from modules.skills.tests.fixture_skills import crafted_tree, run_surface

    code, out, _ = run_surface(crafted_tree(tmp_path), "lint")
    assert code == 1
    assert "[name-mismatch]" in out


def test_acceptance_catalog_builds_and_reads(tmp_path: Path):
    """AC-SKILLS-011: ``catalog`` default builds + reads; ``--read`` alone prints."""
    from modules.skills.tests.fixture_skills import crafted_tree, run_surface

    root = crafted_tree(tmp_path)
    code, out, _ = run_surface(root, "catalog")
    assert code == 0
    assert "Rebuilt" in out
    assert "## Skills" in out

    # --read alone: after a build, the content is present
    code, out, _ = run_surface(root, "catalog", "--read")
    assert code == 0
    assert "## Skills" in out


def test_acceptance_catalog_read_missing_file_exits_1(tmp_path: Path):
    """AC-SKILLS-011b: ``--read`` with no CATALOG.md exits 1."""
    from modules.skills.tests.fixture_skills import crafted_tree, run_surface

    root = crafted_tree(tmp_path)  # no CATALOG.md yet
    code, _out, err = run_surface(root, "catalog", "--read")
    assert code == 1
    assert "CATALOG.md not found" in err


def test_acceptance_discover_finds_a_catalog_row(tmp_path: Path):
    """AC-SKILLS-012: ``discover`` answers from CATALOG.md."""
    from modules.skills.tests.fixture_skills import crafted_tree, run_surface

    root = crafted_tree(tmp_path)
    run_surface(root, "catalog")
    code, out, _ = run_surface(root, "discover", "docs")
    assert code == 0
    assert "| doc-drafts |" in out


def test_acceptance_mutation_verbs_not_in_cli(tmp_path: Path):
    """AC-SKILLS-015: move/archive/create are capability-only, not routed from the CLI."""
    from modules.skills.tests.fixture_skills import crafted_tree, run_surface

    root = crafted_tree(tmp_path)
    for args in (
        ("move", "drafts/doc-drafts", "notes"),
        ("archive", "notes/doc-drafts", "--apply"),
        ("create", "category", "beta-cat", "--description", "Second", "--apply"),
    ):
        code, _out, err = run_surface(root, *args)
        assert code == 2, args
        assert "Unknown skills subcommand" in err, args


def test_acceptance_unknown_subcommand_is_usage_error(tmp_path: Path):
    """AC-SKILLS-018: an unknown verb exits 2, not 1."""
    from modules.skills.tests.fixture_skills import run_surface

    code, _out, err = run_surface(tmp_path, "frobnicate")
    assert code == 2
    assert "Unknown skills subcommand" in err
