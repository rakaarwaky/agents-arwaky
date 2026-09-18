"""Skill provisioning tests — symlink-by-default, copy fallback, link-safe removal.

Covers tools/connect/connect_shared.provision_skill_to_dir and
tools/skill/skill.py provisioning: the invariant is that a provisioned skill
is a LINK into the repo pack (skills/<name>/), so an agent editing it anywhere
writes back to the single source of truth, and removal only ever drops the
link — never the pack.
"""
import json
import os
import shutil
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))




SKILL_BODY = "---\nname: {name}\ndescription: test skill\n---\n\nbody\n"


@pytest.fixture
def pack(tmp_path):
    """A fake repo layout mirroring agents-arwaky: <tmp>/skills/demo-skill/
    SKILL.md (+ assets) as the pack, and <tmp>/harness/skills as the dest.
    REPO_ROOT is patched to <tmp> so the pack-root guard behaves exactly like
    the real tree."""
    src = tmp_path / "skills" / "demo-skill"
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
        import modules.harness.src.capabilities_harness_shared as connect_shared
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
        import modules.harness.src.capabilities_harness_shared as connect_shared
        monkeypatch.setattr(connect_shared, "REPO_ROOT", pack[0].parents[1])
        src, dest_base = pack
        connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base)
        (dest_base / "demo-skill" / "SKILL.md").write_text("IMPROVED")
        assert (src / "SKILL.md").read_text() == "IMPROVED"

    def test_idempotent_relink_skips(self, pack, monkeypatch):
        import modules.harness.src.capabilities_harness_shared as connect_shared
        monkeypatch.setattr(connect_shared, "REPO_ROOT", pack[0].parents[1])
        src, dest_base = pack
        assert connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base) is True
        assert connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base) is False
        assert (dest_base / "demo-skill").is_symlink()

    def test_copy_mode_still_copies(self, pack, monkeypatch):
        import modules.harness.src.capabilities_harness_shared as connect_shared
        monkeypatch.setattr(connect_shared, "REPO_ROOT", pack[0].parents[1])
        src, dest_base = pack
        ok = connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base, link=False)
        assert ok is True
        d = dest_base / "demo-skill"
        assert d.is_dir() and not d.is_symlink()
        assert (d / "SKILL.md").read_text() == SKILL_BODY.format(name="demo-skill")

    def test_identical_copy_is_upgraded_to_link(self, pack, monkeypatch):
        import modules.harness.src.capabilities_harness_shared as connect_shared
        monkeypatch.setattr(connect_shared, "REPO_ROOT", pack[0].parents[1])
        src, dest_base = pack
        connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base, link=False)
        assert connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base) is True
        assert (dest_base / "demo-skill").is_symlink()

    def test_divergent_copy_is_protected(self, pack, monkeypatch):
        """Edited copy without --force: warn, keep it, never destroy the edit."""
        import modules.harness.src.capabilities_harness_shared as connect_shared
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
        import modules.harness.src.capabilities_harness_shared as connect_shared
        monkeypatch.setattr(connect_shared, "REPO_ROOT", pack[0].parents[1])
        src, dest_base = pack
        elsewhere = src.parent / "other"
        elsewhere.mkdir()
        os.symlink(elsewhere, dest_base / "demo-skill", target_is_directory=True)
        assert connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base) is False
        assert (dest_base / "demo-skill").resolve() == elsewhere.resolve()

    def test_self_pack_link_is_refused(self, pack, monkeypatch):
        """Provisioning the pack into itself must not create a self-loop."""
        import modules.harness.src.capabilities_harness_shared as connect_shared
        src, _ = pack
        monkeypatch.setattr(connect_shared, "REPO_ROOT", src.parents[1])
        assert connect_shared.provision_skill_to_dir(src / "SKILL.md", src.parent) is False
        assert not (src / "demo-skill").exists()


# ---------------------------------------------------------------------------
# connect_shared.remove_provisioned_skills
# ---------------------------------------------------------------------------
class TestRemoveProvisioned:
    def test_unlink_keeps_pack_source(self, pack, monkeypatch):
        import modules.harness.src.capabilities_harness_shared as connect_shared
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
        import modules.harness.src.capabilities_harness_shared as connect_shared
        src, dest_base = pack
        monkeypatch.setattr(connect_shared, "REPO_ROOT", src.parents[1])
        monkeypatch.setattr(connect_shared, "get_all_skill_files",
                            lambda: (src / "SKILL.md",))
        connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base)
        assert connect_shared.remove_provisioned_skills(dest_base, dry_run=True) == 1
        assert (dest_base / "demo-skill").is_symlink()


# ---------------------------------------------------------------------------
# connect_shared.link_skills_root  (whole-folder symlink: one place to manage)
# ---------------------------------------------------------------------------
class TestLinkSkillsRoot:
    def test_links_when_absent(self, pack, monkeypatch):
        import modules.harness.src.capabilities_harness_shared as connect_shared
        src, _ = pack
        monkeypatch.setattr(connect_shared, "REPO_ROOT", src.parents[1])
        dest = src.parents[1] / "harness" / "skills-root-missing"
        assert connect_shared.link_skills_root(dest, src.parents[0]) is True
        assert dest.is_symlink() and dest.resolve() == src.parents[0].resolve()

    def test_non_empty_abort_without_force(self, pack, monkeypatch):
        import modules.harness.src.capabilities_harness_shared as connect_shared
        src, dest_base = pack
        monkeypatch.setattr(connect_shared, "REPO_ROOT", src.parents[1])
        (dest_base / "native-skill").mkdir()
        (dest_base / "native-skill" / "SKILL.md").write_text("mine")
        assert connect_shared.link_skills_root(dest_base, src.parent, force=False) is False
        assert (dest_base / "native-skill" / "SKILL.md").is_file()  # untouched
        assert not dest_base.is_symlink()

    def test_force_migrates_leftovers_into_pack(self, pack, monkeypatch):
        import modules.harness.src.capabilities_harness_shared as connect_shared
        src, dest_base = pack
        pack_root = src.parent
        monkeypatch.setattr(connect_shared, "REPO_ROOT", src.parents[1])
        native = dest_base / "native-skill"
        native.mkdir()
        (native / "SKILL.md").write_text("mine")
        assert connect_shared.link_skills_root(dest_base, pack_root, force=True) is True
        assert dest_base.is_symlink()
        assert dest_base.resolve() == pack_root.resolve()
        # leftover moved into the pack and visible THROUGH the link
        assert (pack_root / "native-skill" / "SKILL.md").read_text() == "mine"
        assert (dest_base / "native-skill" / "SKILL.md").is_file()

    def test_stale_per_skill_links_are_unlinked(self, pack, monkeypatch):
        import modules.harness.src.capabilities_harness_shared as connect_shared
        src, dest_base = pack
        pack_root = src.parent
        monkeypatch.setattr(connect_shared, "REPO_ROOT", src.parents[1])
        os.symlink(src, dest_base / "demo-skill", target_is_directory=True)
        assert connect_shared.link_skills_root(dest_base, pack_root, force=True) is True
        assert dest_base.is_symlink()
        assert (src / "SKILL.md").is_file()  # old per-skill link source intact

    def test_idempotent(self, pack, monkeypatch):
        import modules.harness.src.capabilities_harness_shared as connect_shared
        src, dest_base = pack
        pack_root = src.parent
        monkeypatch.setattr(connect_shared, "REPO_ROOT", src.parents[1])
        dest_base.rmdir()
        assert connect_shared.link_skills_root(dest_base, pack_root) is True
        assert connect_shared.link_skills_root(dest_base, pack_root) is False

    def test_disconnect_unlinks_root_keeps_pack(self, pack, monkeypatch):
        import modules.harness.src.capabilities_harness_shared as connect_shared
        src, dest_base = pack
        pack_root = src.parent
        monkeypatch.setattr(connect_shared, "REPO_ROOT", src.parents[1])
        dest_base.rmdir()
        connect_shared.link_skills_root(dest_base, pack_root)
        removed = connect_shared.remove_provisioned_skills(dest_base)
        assert removed == 1
        assert not dest_base.is_symlink()
        assert dest_base.is_dir() and not any(dest_base.iterdir())
        assert (src / "SKILL.md").is_file()

    def test_stale_identical_copy_is_discarded(self, pack, monkeypatch):
        """Copy-mode era snapshot still byte-identical to the pack: the copy
        is dropped and the pack source serves through the root link."""
        import modules.harness.src.capabilities_harness_shared as connect_shared
        src, dest_base = pack
        pack_root = src.parent
        monkeypatch.setattr(connect_shared, "REPO_ROOT", src.parents[1])
        stale = dest_base / "demo-skill"
        stale.mkdir()
        shutil.copy2(src / "SKILL.md", stale / "SKILL.md")
        (stale / "references").mkdir()
        shutil.copy2(src / "references" / "api.md", stale / "references" / "api.md")
        assert connect_shared.link_skills_root(dest_base, pack_root, force=True) is True
        assert not (pack_root / "demo-skill.harness-1").exists()
        assert (dest_base / "demo-skill" / "references" / "api.md").read_text() == "ref"

    def test_divergent_copy_is_stashed_not_clobbering(self, pack, monkeypatch):
        """Harness-side edit: never overwrite the pack, stash for review."""
        import modules.harness.src.capabilities_harness_shared as connect_shared
        src, dest_base = pack
        pack_root = src.parent
        monkeypatch.setattr(connect_shared, "REPO_ROOT", src.parents[1])
        stale = dest_base / "demo-skill"
        stale.mkdir()
        (stale / "SKILL.md").write_text("LOCAL-EDIT")
        assert connect_shared.link_skills_root(dest_base, pack_root, force=True) is True
        assert (pack_root / "demo-skill" / "SKILL.md").read_text() == \
            SKILL_BODY.format(name="demo-skill")  # pack untouched
        assert (pack_root / "demo-skill.harness-1" / "SKILL.md").read_text() == "LOCAL-EDIT"

    def test_state_dir_collision_merges_not_renames(self, pack, monkeypatch):
        """.hub twin in the pack: harness copy wins per-file, no .harness-1 junk."""
        import modules.harness.src.capabilities_harness_shared as connect_shared
        src, dest_base = pack
        pack_root = src.parent
        monkeypatch.setattr(connect_shared, "REPO_ROOT", src.parents[1])
        (pack_root / ".hub").mkdir()
        (pack_root / ".hub" / "taps.json").write_text("pack-empty")
        (pack_root / ".hub" / "quarantine").mkdir()
        h_state = dest_base / ".hub"
        h_state.mkdir()
        (h_state / "taps.json").write_text("harness-live")
        (h_state / "index-cache").mkdir()
        (h_state / "index-cache" / "idx.json").write_text("cache")
        assert connect_shared.link_skills_root(dest_base, pack_root, force=True) is True
        assert dest_base.is_symlink()
        assert not (pack_root / ".hub.harness-1").exists()
        assert (pack_root / ".hub" / "taps.json").read_text() == "harness-live"
        assert (pack_root / ".hub" / "index-cache" / "idx.json").is_file()
        assert (pack_root / ".hub" / "quarantine").is_dir()  # pack-only kept

    def test_per_skill_ops_blocked_on_linked_root(self, pack, monkeypatch):
        """Provisioning/removing INTO a linked root must not rmtree pack dirs."""
        import modules.harness.src.capabilities_harness_shared as connect_shared
        src, dest_base = pack
        pack_root = src.parent
        monkeypatch.setattr(connect_shared, "REPO_ROOT", src.parents[1])
        dest_base.rmdir()
        connect_shared.link_skills_root(dest_base, pack_root)
        assert connect_shared.provision_skill_to_dir(src / "SKILL.md", dest_base) is False
        assert src.is_dir()  # pack source survived the blocked attempt


# ---------------------------------------------------------------------------
# tools/skill/skill.py
# ---------------------------------------------------------------------------
class TestSkillCliProvision:
    @pytest.fixture
    def mod(self, pack, monkeypatch):
        import modules.skill.src.capabilities_skill_registry as skill_mod
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


# ---------------------------------------------------------------------------
# tools/lib/skill_pack.py — provenance, pruning, loadability audit
# ---------------------------------------------------------------------------
@pytest.fixture
def cat_pack(tmp_path):
    """A categorized pack (<tmp>/skills/<category>/<skill>/SKILL.md) plus an
    empty provision target, with skill_pack pointed at it."""
    from modules.shared.src.skill_pack import capabilities_skill_pack as skill_pack
    pack = tmp_path / "skills"
    src = pack / "media" / "demo-skill"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text(SKILL_BODY.format(name="demo-skill"))
    (src / "references").mkdir()
    (src / "references" / "api.md").write_text("ref")
    ws = tmp_path / "ws" / ".agents" / "skills"
    ws.mkdir(parents=True)
    return skill_pack, pack, src, ws


class TestProvenance:
    def test_copy_records_provenance(self, cat_pack):
        """--prune is only safe because every copy says where it came from."""
        import modules.skill.src.capabilities_skill_registry as skill_mod
        skill_pack, pack, src, ws = cat_pack
        skill_mod.PACK_ROOT = pack
        assert skill_mod.provision_single_skill(src / "SKILL.md", ws.parents[1]) is True
        meta = json.loads((ws / "demo-skill" / skill_pack.PROVENANCE_FILE).read_text())
        assert meta["source"] == "media/demo-skill/SKILL.md"
        assert meta["category"] == "media"
        assert meta["name"] == "demo-skill"

    def test_link_writes_no_provenance(self, cat_pack):
        """A link already points at the pack; writing next to it would land in
        the repo and pollute the single source of truth."""
        import modules.skill.src.capabilities_skill_registry as skill_mod
        skill_pack, pack, src, ws = cat_pack
        skill_mod.PACK_ROOT = pack
        assert skill_mod.provision_single_skill(src / "SKILL.md", ws.parents[1], link=True) is True
        assert not (pack / "media" / "demo-skill" / skill_pack.PROVENANCE_FILE).exists()


class TestPrune:
    def test_removes_copy_whose_pack_source_is_gone(self, cat_pack):
        skill_pack, pack, src, ws = cat_pack
        stale = ws / "old-skill"
        stale.mkdir()
        (stale / "SKILL.md").write_text("gone")
        (stale / skill_pack.PROVENANCE_FILE).write_text(json.dumps(
            {"version": 1, "name": "old-skill", "source": "media/old-skill/SKILL.md"}))
        assert skill_pack.prune_provisioned(ws, pack) == ["old-skill"]
        assert not stale.exists()

    def test_keeps_hand_written_skill(self, cat_pack):
        """No provenance means the tool never placed it — never delete it."""
        skill_pack, pack, _, ws = cat_pack
        handmade = ws / "my-own-skill"
        handmade.mkdir()
        (handmade / "SKILL.md").write_text("mine")
        assert skill_pack.prune_provisioned(ws, pack) == []
        assert handmade.is_dir()

    def test_dangling_pack_link_goes_foreign_link_stays(self, cat_pack):
        skill_pack, pack, _, ws = cat_pack
        dead = ws / "retired-skill"
        dead.symlink_to(pack / "media" / "retired-skill", target_is_directory=True)
        foreign = ws / "elsewhere"
        foreign.symlink_to(Path("/etc/hostname"))
        assert skill_pack.prune_provisioned(ws, pack) == ["retired-skill"]
        assert not dead.exists() and dead.is_symlink() is False
        assert foreign.is_symlink()

    def test_live_pack_link_survives(self, cat_pack):
        skill_pack, pack, src, ws = cat_pack
        (ws / "demo-skill").symlink_to(src, target_is_directory=True)
        assert skill_pack.prune_provisioned(ws, pack) == []
        assert (ws / "demo-skill" / "SKILL.md").is_file()


class TestPackAudit:
    def test_clean_pack_has_no_findings(self, cat_pack):
        skill_pack, pack, _, _ = cat_pack
        assert skill_pack.audit_pack(pack) == []

    def test_flags_flat_nesting_and_duplicate_names(self, tmp_path):
        skill_pack = _skill_pack()
        pack = tmp_path / "skills"
        for name, body in {
            "cat/a": "---\nname: a\ndescription: ok\n---\n",
            "loose": "---\nname: a\ndescription: also a\n---\n",
            "cat/mismatch": "---\nname: other\ndescription: ok\n---\n",
            "cat/nodesc": "---\nname: nodesc\ndescription:\n---\n",
        }.items():
            folder = pack.joinpath(*name.split("/"))
            folder.mkdir(parents=True)
            (folder / "SKILL.md").write_text(body)
        (pack / "cat" / "no-skill-file").mkdir(parents=True)
        (pack / "empty-category").mkdir(parents=True)
        codes = {f.code for f in skill_pack.audit_pack(pack)}
        assert {"nested-layout", "name-mismatch", "duplicate-name",
                "description-missing", "empty-category",
                "skill-without-skill-md"} <= codes

    def test_description_budget_is_enforced(self, tmp_path, monkeypatch):
        skill_pack = _skill_pack()
        monkeypatch.setattr(skill_pack, "DESCRIPTION_BUDGET_BYTES", 4)
        pack = tmp_path / "skills"
        (pack / "cat" / "a").mkdir(parents=True)
        (pack / "cat" / "a" / "SKILL.md").write_text(
            "---\nname: a\ndescription: far too long for the budget\n---\n")
        assert "description-budget" in {f.code for f in skill_pack.audit_pack(pack)}

    def test_shipped_pack_passes_its_own_gate(self):
        """The real skills/ tree must satisfy every invariant aa check asserts."""
        root = Path(__file__).resolve().parents[2]
        skill_pack = _skill_pack()
        findings = skill_pack.audit_pack(root / "skills")
        assert findings == [], [f.code for f in findings]


class TestToolResolution:
    def test_handle_matches_are_word_bounded(self, tmp_path):
        """'vision' must not be claimed by a skill merely containing 'provisioning'."""
        import modules.skill.src.capabilities_skill_registry as skill_mod
        pack = tmp_path / "skills" / "media" / "vision-arwaky"
        pack.mkdir(parents=True)
        (pack / "SKILL.md").write_text(SKILL_BODY.format(name="vision-arwaky"))
        noise = tmp_path / "skills" / "automation" / "chromium-profile-provisioning"
        noise.mkdir(parents=True)
        (noise / "SKILL.md").write_text(
            "---\nname: chromium-profile-provisioning\n"
            "description: Create or inspect Brave/Chromium profile dirs.\n---\n")
        skill_mod._get_all_skills.cache_clear()
        skill_mod.REPO_ROOT = tmp_path
        skill_mod.PACK_ROOT = tmp_path / "skills"
        try:
            hits = skill_mod.resolve_tool_skills({"id": "vision", "alias": "va"})
            assert [p.parent.name for p in hits] == ["vision-arwaky"]
        finally:
            skill_mod._get_all_skills.cache_clear()


def _skill_pack():
    from modules.shared.src.skill_pack import capabilities_skill_pack as skill_pack
    return skill_pack

