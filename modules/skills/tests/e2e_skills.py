"""E2E tests for modules/skills — full CLI dispatch path."""
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


def test_e2e_dispatch_list(tmp_path: Path, monkeypatch):
    """E2E-SKILLS-001: `aa skills list` dispatches and exits 0."""
    import modules.skills.src.capabilities_skills_index_builder as builder_mod
    import modules.skills.src.capabilities_skills_pack_reader as reader_mod
    from modules.root_cli_entry import _dispatch

    pack = _make_pack(tmp_path)
    monkeypatch.setattr(builder_mod, "default_pack_root", lambda: pack)
    monkeypatch.setattr(reader_mod, "default_pack_root", lambda: pack)
    rc = _dispatch(["skills", "list"])
    assert rc == 0


def test_e2e_dispatch_show(tmp_path: Path, monkeypatch):
    """E2E-SKILLS-002: `aa skills show <name>` dispatches and exits 0."""
    import modules.skills.src.capabilities_skills_index_builder as builder_mod
    import modules.skills.src.capabilities_skills_pack_reader as reader_mod
    from modules.root_cli_entry import _dispatch

    pack = _make_pack(tmp_path)
    monkeypatch.setattr(builder_mod, "default_pack_root", lambda: pack)
    monkeypatch.setattr(reader_mod, "default_pack_root", lambda: pack)
    rc = _dispatch(["skills", "show", "fetch-mcp"])
    assert rc == 0


def test_e2e_dispatch_validate_and_catalog(tmp_path: Path):
    """E2E-SKILLS-003: `aa skills validate|catalog` dispatch end to end."""
    from modules.root_cli_entry import _dispatch
    from modules.skills.tests.support_skills import crafted_tree

    root = crafted_tree(tmp_path)
    assert _dispatch(["skills", "validate", "--skills-root", str(root)]) == 1
    assert _dispatch(["skills", "catalog", "--skills-root", str(root)]) == 0
    assert _dispatch(["skills", "catalog", "--check", "--skills-root", str(root)]) == 0


def test_e2e_dispatch_authoring_read_only_verbs(tmp_path: Path):
    """E2E-SKILLS-005: discover / weed / merge-plan / rules dispatch and exit 0."""
    from modules.root_cli_entry import _dispatch
    from modules.skills.tests.support_skills import crafted_tree

    root = crafted_tree(tmp_path)
    root_arg = ["--skills-root", str(root)]
    _dispatch(["skills", "catalog", *root_arg])
    assert _dispatch(["skills", "discover", "notes", *root_arg]) == 0
    assert _dispatch(["skills", "weed", *root_arg]) == 0
    assert (
        _dispatch(
            [
                "skills",
                "merge-plan",
                "drafts/doc-drafts",
                "notes/note-taker",
                *root_arg,
            ]
        )
        == 0
    )
    assert _dispatch(["skills", "rules", *root_arg]) == 0


def test_e2e_dispatch_move_applies_then_rebuilds_catalog(tmp_path: Path):
    """E2E-SKILLS-006: move --apply moves the folder and the agent's
    post-apply rebuild leaves CATALOG.md in sync (drift check exits 0)."""
    from modules.root_cli_entry import _dispatch
    from modules.skills.tests.support_skills import crafted_tree

    root = crafted_tree(tmp_path)
    root_arg = ["--skills-root", str(root)]
    _dispatch(["skills", "catalog", *root_arg])

    assert (
        _dispatch(
            [
                "skills",
                "move",
                "drafts/doc-drafts",
                "notes",
                "--apply",
                *root_arg,
            ]
        )
        == 0
    )
    assert (root / "notes" / "doc-drafts" / "SKILL.md").exists()
    assert not (root / "drafts" / "doc-drafts").exists()
    assert _dispatch(["skills", "catalog", "--check", *root_arg]) == 0


def test_e2e_dispatch_new_category_dry_run_then_apply(tmp_path: Path):
    """E2E-SKILLS-007: new-category previews without writing, then --apply creates it."""
    from modules.root_cli_entry import _dispatch
    from modules.skills.tests.support_skills import crafted_tree

    root = crafted_tree(tmp_path)
    root_arg = ["--skills-root", str(root)]

    assert _dispatch(["skills", "new-category", "beta", "Beta", *root_arg]) == 0
    assert not (root / "beta").exists()

    assert _dispatch(["skills", "new-category", "beta", "Beta", "--apply", *root_arg]) == 0
    assert (root / "beta" / "DESCRIPTION.md").exists()


def test_e2e_dispatch_unknown_subcommand_is_2():
    """E2E-SKILLS-004: the flagged exit-code change holds through dispatch."""
    from modules.root_cli_entry import _dispatch

    assert _dispatch(["skills", "frobnicate"]) == 2
