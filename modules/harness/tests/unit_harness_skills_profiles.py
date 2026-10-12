"""Regression: aa connect --hermes --skills-only must link the skill pack
into the default Hermes home AND every named profile's skills dir.

Named profiles are isolated HERMES_HOMEs — they do NOT inherit
``~/.hermes/skills`` — so each ``~/.hermes/profiles/<p>/skills`` must be
linked independently.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from modules.harness.src.capabilities_harness_skills import (
    HarnessSkills,
    _skills_targets_for,
)
from modules.shared.src.taxonomy_common_constant import REPO_ROOT


def _multi_profile_adapter(root: Path) -> SimpleNamespace:
    """Hermes-shaped adapter: one skills dir per profile under root/profiles."""
    profiles = root / "profiles"

    def skills_targets():
        targets = [("Default Profile", root / "skills")]
        if profiles.is_dir():
            for p in sorted(profiles.iterdir()):
                if p.is_dir():
                    targets.append((f"Profile: {p.name}", p / "skills"))
        return tuple(targets)

    return SimpleNamespace(
        id="hermes",
        display="Hermes Agent",
        skill_link_verified=True,
        skills_dir=lambda: root / "skills",
        skills_targets=skills_targets,
    )


def test_skills_targets_fallback_single_dir(tmp_path):
    """An adapter without skills_targets() falls back to its one skills_dir."""
    adapter = SimpleNamespace(id="grok-build", display="Grok", skills_dir=lambda: tmp_path / "skills")
    assert _skills_targets_for(adapter) == [("grok-build", tmp_path / "skills")]


def test_skills_targets_collects_profiles(tmp_path):
    """An adapter with skills_targets() reports every profile dir."""
    (tmp_path / "profiles" / "alpha").mkdir(parents=True)
    (tmp_path / "profiles" / "beta").mkdir(parents=True)
    targets = _skills_targets_for(_multi_profile_adapter(tmp_path))
    labels = [label for label, _ in targets]
    assert "Default Profile" in labels
    assert "Profile: alpha" in labels
    assert "Profile: beta" in labels


def test_provision_skills_links_default_home_and_every_profile(tmp_path):
    """provision_skills (aa connect path): default home + each profile linked."""
    (tmp_path / "profiles" / "alpha").mkdir(parents=True)
    (tmp_path / "profiles" / "beta").mkdir(parents=True)
    skills = HarnessSkills({"hermes": _multi_profile_adapter(tmp_path)})
    assert skills.provision_skills(("hermes",)) == 0
    pack = REPO_ROOT / "skills"
    for dest in (tmp_path / "skills",
                 tmp_path / "profiles" / "alpha" / "skills",
                 tmp_path / "profiles" / "beta" / "skills"):
        assert dest.is_symlink(), f"{dest} not linked"
        assert dest.resolve() == pack.resolve(), f"{dest} -> {dest.resolve()}"


def test_provision_skills_idempotent_across_profiles(tmp_path):
    """Re-running against already-linked profiles is a no-op, not an error."""
    (tmp_path / "profiles" / "alpha").mkdir(parents=True)
    skills = HarnessSkills({"hermes": _multi_profile_adapter(tmp_path)})
    assert skills.provision_skills(("hermes",)) == 0
    assert skills.provision_skills(("hermes",)) == 0
    assert (tmp_path / "profiles" / "alpha" / "skills").is_symlink()
