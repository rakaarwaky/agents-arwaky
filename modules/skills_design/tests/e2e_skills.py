"""E2E tests for modules/skills_design — full CLI dispatch path."""
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
    import modules.skills_design.src.capabilities_skills_lister as lister_mod
    import modules.skills_design.src.capabilities_skills_reader as reader_mod
    from modules.root_cli_entry import _dispatch

    pack = _make_pack(tmp_path)
    monkeypatch.setattr(lister_mod, "default_pack_root", lambda: pack)
    monkeypatch.setattr(reader_mod, "default_pack_root", lambda: pack)
    rc = _dispatch(["skills", "list"])
    assert rc == 0


def test_e2e_dispatch_read(tmp_path: Path, monkeypatch):
    """E2E-SKILLS-002: `aa skills read <name>` dispatches and exits 0."""
    import modules.skills_design.src.capabilities_skills_lister as lister_mod
    import modules.skills_design.src.capabilities_skills_reader as reader_mod
    from modules.root_cli_entry import _dispatch

    pack = _make_pack(tmp_path)
    monkeypatch.setattr(lister_mod, "default_pack_root", lambda: pack)
    monkeypatch.setattr(reader_mod, "default_pack_root", lambda: pack)
    rc = _dispatch(["skills", "read", "fetch-mcp"])
    assert rc == 0


def test_e2e_dispatch_lint(tmp_path: Path):
    """E2E-SKILLS-003: `aa skills lint` dispatches end to end."""
    from modules.root_cli_entry import _dispatch
    from modules.skills_design.tests.fixture_skills import crafted_tree

    crafted_tree(tmp_path)
    # lint runs against the default pack root (repo skills/); the crafted
    # tree is only relevant for in-process tests. Here we just confirm the
    # dispatch path exits 0 on a clean repo pack or 1 on a real issue.
    rc = _dispatch(["skills", "lint"])
    assert rc in (0, 1)


def test_e2e_dispatch_catalog_default(tmp_path: Path):
    """E2E-SKILLS-003b: `aa skills catalog` (default: build + read) exits 0."""
    from modules.root_cli_entry import _dispatch

    rc = _dispatch(["skills", "catalog"])
    assert rc == 0


def test_e2e_dispatch_catalog_build_only(tmp_path: Path):
    """E2E-SKILLS-003c: `aa skills catalog --build` exits 0."""
    from modules.root_cli_entry import _dispatch

    rc = _dispatch(["skills", "catalog", "--build"])
    assert rc == 0


def test_e2e_dispatch_catalog_read_only(tmp_path: Path):
    """E2E-SKILLS-003d: `aa skills catalog --read` exits 0 after a build."""
    from modules.root_cli_entry import _dispatch

    _dispatch(["skills", "catalog", "--build"])
    rc = _dispatch(["skills", "catalog", "--read"])
    assert rc == 0


def test_e2e_dispatch_discover(tmp_path: Path):
    """E2E-SKILLS-005: discover dispatches and exits 0."""
    from modules.root_cli_entry import _dispatch

    _dispatch(["skills", "catalog", "--build"])
    assert _dispatch(["skills", "discover", "skills"]) == 0


def test_e2e_dispatch_dropped_verbs_exit_2():
    """E2E-SKILLS-005b: move/archive/create/traces are not routed from the CLI."""
    from modules.root_cli_entry import _dispatch

    for sub in ("move", "archive", "create", "traces"):
        assert _dispatch(["skills", sub, "x"]) == 2, sub


def test_e2e_dispatch_unknown_subcommand_is_2():
    """E2E-SKILLS-004: the flagged exit-code change holds through dispatch."""
    from modules.root_cli_entry import _dispatch

    assert _dispatch(["skills", "frobnicate"]) == 2
