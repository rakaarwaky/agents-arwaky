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
    from modules.skills.src.capabilities_skills_index_builder import (
    SkillsIndexBuilder,
)

    rows = list(SkillsIndexBuilder(_make_pack(tmp_path)).list_skills())
    assert [r.name for r in rows] == ["fetch-mcp"]


def test_acceptance_fr_skill_lookup(tmp_path: Path):
    """AC-SKILLS-002: FR-003 — a discovered skill's content is retrievable."""
    from modules.shared.src.skills.taxonomy_skills_vo import SkillQuery
    from modules.skills.src.capabilities_skills_pack_reader import SkillsPackReader

    pack = _make_pack(tmp_path)
    content = SkillsPackReader(pack).show_skill(SkillQuery("fetch-mcp"))
    assert content is not None
    assert "fetch-mcp" in content
    assert "Scrapes web to markdown" in content


def test_acceptance_fr_skill_unknown(tmp_path: Path):
    """AC-SKILLS-003: FR-003 — an unknown skill name returns None."""
    from modules.shared.src.skills.taxonomy_skills_vo import SkillQuery
    from modules.skills.src.capabilities_skills_pack_reader import SkillsPackReader

    pack = _make_pack(tmp_path)
    content = SkillsPackReader(pack).show_skill(SkillQuery("nope-missing"))
    assert content is None

# ─── Authoring acceptance (one case per `aa skills` subcommand) ────────
def test_acceptance_validate_reports_and_exits(tmp_path: Path):
    """AC-SKILLS-010: ``validate`` reports the crafted issue with exit 1."""
    from modules.skills.tests.fixture_skills import crafted_tree, run_surface

    code, out, _ = run_surface(crafted_tree(tmp_path), "validate")
    assert code == 1
    assert "[name-mismatch]" in out


def test_acceptance_catalog_rebuilds_and_checks(tmp_path: Path):
    """AC-SKILLS-011: ``catalog`` rebuilds; ``catalog --check`` gates drift."""
    from modules.skills.tests.fixture_skills import crafted_tree, run_surface

    root = crafted_tree(tmp_path)
    assert run_surface(root, "catalog")[0] == 0
    assert run_surface(root, "catalog", "--check")[0] == 0

    (root / "notes" / "note-taker" / "SKILL.md").write_text(
        "---\nname: note-taker\ndescription: changed\n---\n", encoding="utf-8"
    )
    assert run_surface(root, "catalog", "--check")[0] == 3


def test_acceptance_discover_finds_a_catalog_row(tmp_path: Path):
    """AC-SKILLS-012: ``discover`` answers from CATALOG.md."""
    from modules.skills.tests.fixture_skills import crafted_tree, run_surface

    root = crafted_tree(tmp_path)
    run_surface(root, "catalog")
    code, out, _ = run_surface(root, "discover", "docs")
    assert code == 0
    assert "| doc-drafts |" in out


def test_acceptance_weed_is_clean_on_a_healthy_tree(tmp_path: Path):
    """AC-SKILLS-013: ``weed`` exits 0 when there is nothing to weed."""
    from modules.skills.tests.fixture_skills import crafted_tree, run_surface

    code, out, _ = run_surface(crafted_tree(tmp_path), "weed")
    assert code == 0
    assert "No obvious weeds found." in out


def test_acceptance_repair_defaults_to_preview(tmp_path: Path):
    """AC-SKILLS-014: ``repair`` previews and writes only with ``--apply``."""
    from modules.skills.tests.fixture_skills import crafted_tree, run_surface

    root = crafted_tree(tmp_path)
    code, out, _ = run_surface(root, "repair")
    assert code == 0
    assert "dry-run" in out
    assert "name: wrong-name" in (
        root / "drafts" / "doc-drafts" / "SKILL.md"
    ).read_text(encoding="utf-8")

    code, out, _ = run_surface(root, "repair", "--apply")
    assert code == 0
    assert "Repairs applied:" in out


def test_acceptance_move_archive_new_category(tmp_path: Path):
    """AC-SKILLS-015: the three path mutations preview and apply."""
    from modules.skills.tests.fixture_skills import crafted_tree, run_surface

    root = crafted_tree(tmp_path)
    assert run_surface(root, "move", "drafts/doc-drafts", "notes")[0] == 0
    assert run_surface(root, "move", "drafts/doc-drafts", "notes", "--apply")[0] == 0
    assert (root / "notes" / "doc-drafts").exists()

    assert run_surface(root, "archive", "notes/doc-drafts", "--apply")[0] == 0
    assert (root / "_archive" / "notes" / "doc-drafts" / "SKILL.md.archived").exists()

    assert run_surface(root, "new-category", "beta-cat", "Second", "--apply")[0] == 0
    assert (root / "beta-cat" / "DESCRIPTION.md").exists()


def test_acceptance_merge_plan_is_read_only(tmp_path: Path):
    """AC-SKILLS-016: ``merge-plan`` emits a plan and changes nothing."""
    from modules.skills.tests.fixture_skills import crafted_tree, run_surface

    root = crafted_tree(tmp_path)
    code, out, _ = run_surface(
        root, "merge-plan", "drafts/doc-drafts", "notes/note-taker"
    )
    assert code == 0
    assert out.startswith("# Merge plan")
    assert (root / "drafts" / "doc-drafts").exists()


def test_acceptance_rules_render_the_ssot(tmp_path: Path):
    """AC-SKILLS-017: ``rules`` renders one line per rule."""
    from modules.skills.tests.fixture_skills import crafted_tree, run_surface

    code, out, _ = run_surface(crafted_tree(tmp_path), "rules")
    assert code == 0
    assert out.count("- [error]") == 13


def test_acceptance_unknown_subcommand_is_usage_error(tmp_path: Path):
    """AC-SKILLS-018: an unknown verb exits 2, not 1."""
    from modules.skills.tests.fixture_skills import run_surface

    code, _out, err = run_surface(tmp_path, "frobnicate")
    assert code == 2
    assert "Unknown skills subcommand" in err
