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
