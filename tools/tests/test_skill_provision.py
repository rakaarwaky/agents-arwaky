"""Skill provisioning tests — symlink-by-default, copy fallback, link-safe removal.

Covers tools/connect/connect_shared.provision_skill_to_dir and
tools/skill/skill.py provisioning: the invariant is that a provisioned skill
is a LINK into the repo pack (skills/<name>/), so an agent editing it anywhere
writes back to the single source of truth, and removal only ever drops the
link — never the pack.
"""
import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "lib"))
sys.path.insert(0, str(_ROOT / "connect"))
sys.path.insert(0, str(_ROOT / "skill"))


SKILL_BODY = "---\nname: {name}\ndescription: test skill\n---\n\nbody\n"


@pytest.fixture
def pack(tmp_path):
    """A fake repo pack: <root>/skills/<cat-name>/SKILL.md (+ assets)."""
    src = tmp_path / "pack" / "demo-skill"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text(SKILL_BODY.format(name="demo-skill"))
    (src / "references").mkdir()
    (src / "references" / "api.md").write_text("ref")
    dest = tmp_path / "harness" / "skills"
    dest.mkdir(parents=True)
    return src, dest


# ---------------------------------------------------------------------------
# connect_shared.provision_skill_to_dir
# ---------------------------------------------------------------------------
class TestProvisionLink:
    def test_default_links_skill_dir(self, pack, monkeypatch):
        import connect_shared
        monkeypatch.setattr(connect_shared, "REPO_ROOT", pack[0].parents[1])
        src, dest_base = pack
        ok = connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base)
        assert ok is True
        link = dest_base / "demo-skill"
        assert link.is_symlink()
        assert link.resolve() == src.resolve()
        assert (link / "references" / "api.md").read_text() == "ref"

    def test_edit_through_link_reaches_pack(self, pack, monkeypatch):
        """The self-improvement loop: harness-side write lands in the repo pack."""
        import connect_shared
        monkeypatch.setattr(connect_shared, "REPO_ROOT", pack[0].parents[1])
        src, dest_base = pack
        connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base)
        (dest_base / "demo-skill" / "SKILL.md").write_text("IMPROVED")
        assert (src / "SKILL.md").read_text() == "IMPROVED"

    def test_idempotent_relink_skips(self, pack, monkeypatch):
        import connect_shared
        monkeypatch.setattr(connect_shared, "REPO_ROOT", pack[0].parents[1])
        src, dest_base = pack
        assert connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base) is True
        assert connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base) is False
        assert (dest_base / "demo-skill").is_symlink()

    def test_copy_mode_still_copies(self, pack, monkeypatch):
        import connect_shared
        monkeypatch.setattr(connect_shared, "REPO_ROOT", pack[0].parents[1])
        src, dest_base = pack
        ok = connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base, link=False)
        assert ok is True
        d = dest_base / "demo-skill"
        assert d.is_dir() and not d.is_symlink()
        assert (d / "SKILL.md").read_text() == SKILL_BODY.format(name="demo-skill")

    def test_identical_copy_is_upgraded_to_link(self, pack, monkeypatch):
        import connect_shared
        monkeypatch.setattr(connect_shared, "REPO_ROOT", pack[0].parents[1])
        src, dest_base = pack
        connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base, link=False)
        assert connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base) is True
        assert (dest_base / "demo-skill").is_symlink()

    def test_divergent_copy_is_protected(self, pack, monkeypatch):
        """Edited copy without --force: warn, keep it, never destroy the edit."""
        import connect_shared
        monkeypatch.setattr(connect_shared, "REPO_ROOT", pack[0].parents[1])
        src, dest_base = pack
        connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base, link=False)
        (dest_base / "demo-skill" / "SKILL.md").write_text("LOCAL-EDIT")
        assert connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base) is False
        assert (dest_base / "demo-skill" / "SKILL.md").read_text() == "LOCAL-EDIT"
        assert not (dest_base / "demo-skill").is_symlink()
        # with --force the edit is discarded deliberately
        assert connect_shared.provision_skill_to_dir(
            src / "SKILL.md", dest_base, force=True) is True
        assert (dest_base / "demo-skill").is_symlink()

    def test_wrong_target_link_is_rejected(self, pack, monkeypatch):
        import connect_shared
        monkeypatch.setattr(connect_shared, "REPO_ROOT", pack[0].parents[1])
        src, dest_base = pack
        elsewhere = src.parent / "other"
        elsewhere.mkdir()
        os.symlink(elsewhere, dest_base / "demo-skill", target_is_directory=True)
        assert connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base) is False
        assert (dest_base / "demo-skill").resolve() == elsewhere.resolve()

    def test_self_pack_link_is_refused(self, pack, monkeypatch):
        """Provisioning the pack into itself must not create a self-loop."""
        import connect_shared
        src, _ = pack
        monkeypatch.setattr(connect_shared, "REPO_ROOT", src.parents[1])
        assert connect_shared.provision_skill_to_dir(src / "SKILL.md", src.parent) is False
        assert not (src / "demo-skill").exists()


# ---------------------------------------------------------------------------
# connect_shared.remove_provisioned_skills
# ---------------------------------------------------------------------------
class TestRemoveProvisioned:
    def test_unlink_keeps_pack_source(self, pack, monkeypatch):
        import connect_shared
        src, dest_base = pack
        monkeypatch.setattr(connect_shared, "REPO_ROOT", src.parents[1])
        monkeypatch.setattr(connect_shared, "get_all_skill_files",
                            lambda: (src / "SKILL.md",))
        connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base)
        removed = connect_shared.remove_provisioned_skills(dest_base)
        assert removed == 1
        assert not (dest_base / "demo-skill").exists()
        assert (src / "SKILL.md").is_file()  # pack survived

    def test_dry_run_removes_nothing(self, pack, monkeypatch):
        import connect_shared
        src, dest_base = pack
        monkeypatch.setattr(connect_shared, "REPO_ROOT", src.parents[1])
        monkeypatch.setattr(connect_shared, "get_all_skill_files",
                            lambda: (src / "SKILL.md",))
        connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base)
        assert connect_shared.remove_provisioned_skills(dest_base, dry_run=True) == 1
        assert (dest_base / "demo-skill").is_symlink()


# ---------------------------------------------------------------------------
# tools/skill/skill.py
# ---------------------------------------------------------------------------
class TestSkillCliProvision:
    @pytest.fixture
    def mod(self, pack, monkeypatch):
        import skill as skill_mod
        src, _ = pack
        monkeypatch.setattr(skill_mod, "REPO_ROOT", src.parents[1])
        return skill_mod, src

    def test_install_copies_by_default_for_projects(self, mod, tmp_path):
        """Project workspaces get committed — default must be a real copy."""
        skill_mod, src = mod
        ws = tmp_path / "ws"
        assert skill_mod.provision_single_skill(src / "SKILL.md", ws) is True
        d = ws / ".agents" / "skills" / "demo-skill"
        assert d.is_dir() and not d.is_symlink()
        assert (d / "SKILL.md").read_text() == SKILL_BODY.format(name="demo-skill")

    def test_link_flag_opts_in(self, mod, tmp_path):
        skill_mod, src = mod
        ws = tmp_path / "ws"
        assert skill_mod.provision_single_skill(src / "SKILL.md", ws, link=True) is True
        link = ws / ".agents" / "skills" / "demo-skill"
        assert link.is_symlink() and (link / "SKILL.md").is_file()

    def test_uninstall_unlink_keeps_pack(self, mod, tmp_path):
        skill_mod, src = mod
        ws = tmp_path / "ws"
        skill_mod.provision_single_skill(src / "SKILL.md", ws)
        assert skill_mod.remove_single_skill(src / "SKILL.md", ws) is True
        assert not (ws / ".agents" / "skills" / "demo-skill").exists()
        assert (src / "SKILL.md").is_file()

    def test_uninstall_copy_dir_keeps_pack(self, mod, tmp_path):
        skill_mod, src = mod
        ws = tmp_path / "ws"
        skill_mod.provision_single_skill(src / "SKILL.md", ws, link=False)
        assert skill_mod.remove_single_skill(src / "SKILL.md", ws) is True
        assert not (ws / ".agents" / "skills" / "demo-skill").exists()
        assert (src / "SKILL.md").is_file()

    def test_traversal_name_is_neutralized(self, mod, tmp_path):
        """A crafted frontmatter name is sanitized into the skills base, never
        written outside it (escape attempt becomes a plain 'escape' dir)."""
        skill_mod, src = mod
        evil = tmp_path / "evil"
        evil.mkdir()
        (evil / "SKILL.md").write_text('---\nname: ../../escape\n---\n')
        ws = tmp_path / "ws"
        assert skill_mod.provision_single_skill(evil / "SKILL.md", ws) is True
        assert (ws / ".agents" / "skills" / "escape" / "SKILL.md").is_file()
        assert not (tmp_path / "escape").exists()
