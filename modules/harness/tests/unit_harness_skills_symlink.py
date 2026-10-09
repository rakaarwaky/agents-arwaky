"""Regression: aa connect --grok-build --skills-only must create the whole-root
skills symlink even when the harness has never created its skills dir."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from modules.harness.src.capabilities_harness_skills import (
    HarnessSkills,
    _link_skills_root,
)
from modules.shared.src.taxonomy_common_constant import REPO_ROOT


def _adapter(tmp_path: Path) -> SimpleNamespace:
    """Link-verified adapter pointing its skills dir at *tmp_path*/skills."""
    return SimpleNamespace(
        id="grok-build",
        display="Grok Build",
        skill_link_verified=True,
        skills_dir=lambda: tmp_path / "skills",
    )


def test_link_skills_root_creates_symlink_when_absent(tmp_path):
    """_link_skills_root: missing dest -> parent created, symlink lands."""
    dest = tmp_path / "skills"
    failures = _link_skills_root(dest, REPO_ROOT / "skills", force=False, dry_run=False)
    assert failures == 0
    assert dest.is_symlink()
    assert dest.resolve() == (REPO_ROOT / "skills").resolve()


def test_link_skills_root_idempotent_when_linked(tmp_path):
    """_link_skills_root: re-run on the same link is a no-op, not an error."""
    dest = tmp_path / "skills"
    assert _link_skills_root(dest, REPO_ROOT / "skills", force=False, dry_run=False) == 0
    assert _link_skills_root(dest, REPO_ROOT / "skills", force=False, dry_run=False) == 0
    assert dest.is_symlink()


def test_provision_skills_creates_root_symlink_when_dir_absent(tmp_path):
    """provision_skills (the aa connect path): absent skills dir -> created + linked."""
    skills = HarnessSkills({"grok-build": _adapter(tmp_path)})
    assert skills.provision_skills(("grok-build",)) == 0
    link = tmp_path / "skills"
    assert link.is_symlink()
    assert link.resolve() == (REPO_ROOT / "skills").resolve()


def test_provision_skills_idempotent_rerun(tmp_path):
    """provision_skills re-run: no error, link stays, no duplicate dirs."""
    skills = HarnessSkills({"grok-build": _adapter(tmp_path)})
    assert skills.provision_skills(("grok-build",)) == 0
    assert skills.provision_skills(("grok-build",)) == 0
    link = tmp_path / "skills"
    assert link.is_symlink()
    assert link.resolve() == (REPO_ROOT / "skills").resolve()
    assert not (tmp_path / "skills" / "skills").exists()
