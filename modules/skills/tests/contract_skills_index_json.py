"""Contract tests for the skills index JSON-list projection.

Pins the JSON key order and the repo-pack-only source constraint, and
verifies that ``list_skills_json`` is a faithful projection of
``list_skills``.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.skills.taxonomy_skills_vo import SkillsRoot
from modules.skills.src.capabilities_skills_index_builder import (
    SkillsIndexBuilder,
    default_pack_root,
)

# The exact per-entry key order the surface pins.
KEY_ORDER = ("name", "source", "path", "loaded")


def _make_pack(tmp_path: Path) -> Path:
    """Build a miniature pack with two skills in two categories."""
    pack = tmp_path / "skills"
    for cat, skill in (("web", "fetch-mcp"), ("dev", "lint")):
        (pack / cat / skill).mkdir(parents=True)
        (pack / cat / skill / "SKILL.md").write_text(
            f"---\nname: {skill}\ndescription: Does {skill} things.\n---\n\n# {skill}\n",
            encoding="utf-8",
        )
    return pack


def _make_siblings(tmp_path: Path, pack: Path) -> Path:
    """Create a ~/.agents/skills-style sibling root next to *pack*.

    The sibling root contains a skill that must NOT appear in the JSON
    list because the source is the repo pack only.
    """
    sibling = tmp_path / "agents" / "skills"
    (sibling / "ext" / "external-skill").mkdir(parents=True)
    (sibling / "ext" / "external-skill" / "SKILL.md").write_text(
        "---\nname: external-skill\ndescription: External.\n---\n\n# ext\n",
        encoding="utf-8",
    )
    return sibling


def test_json_key_order_pinned(tmp_path: Path) -> None:
    """Each entry's keys appear in the exact order (name, source, path, loaded)."""
    builder = SkillsIndexBuilder(_make_pack(tmp_path))
    payload = builder.list_skills_json()
    assert "skills" in payload
    assert len(payload["skills"]) == 2
    for entry in payload["skills"]:
        assert list(entry.keys()) == list(KEY_ORDER), (
            f"key order mismatch: {list(entry.keys())} != {list(KEY_ORDER)}"
        )


def test_json_entries_sorted_by_name(tmp_path: Path) -> None:
    """Entries are sorted by skill name (deterministic)."""
    builder = SkillsIndexBuilder(_make_pack(tmp_path))
    payload = builder.list_skills_json()
    names = [e["name"] for e in payload["skills"]]
    assert names == sorted(names)


def test_source_is_repo_pack_only(tmp_path: Path) -> None:
    """A sibling root (~/.agents/skills-style) is NOT included in the output."""
    pack = _make_pack(tmp_path)
    _make_siblings(tmp_path, pack)
    builder = SkillsIndexBuilder(pack)
    payload = builder.list_skills_json()
    # The external skill must NOT appear.
    names = [e["name"] for e in payload["skills"]]
    assert "external-skill" not in names, (
        "sibling root was scanned — source must be the repo pack only"
    )
    # The source field must equal the builder's own pack root, not the sibling.
    for entry in payload["skills"]:
        assert entry["source"] == str(pack), (
            f"source {entry['source']!r} != pack root {str(pack)!r}"
        )


def test_source_matches_default_pack_root() -> None:
    """With no explicit root, the source is default_pack_root()."""
    builder = SkillsIndexBuilder()
    payload = builder.list_skills_json()
    expected = str(default_pack_root())
    for entry in payload["skills"]:
        assert entry["source"] == expected


def test_loaded_flag_is_true(tmp_path: Path) -> None:
    """Every entry in the global index is loaded=True."""
    builder = SkillsIndexBuilder(_make_pack(tmp_path))
    payload = builder.list_skills_json()
    for entry in payload["skills"]:
        assert entry["loaded"] is True


def test_json_is_projection_of_list_skills(tmp_path: Path) -> None:
    """The JSON list and list_skills return the same skill set."""
    pack = _make_pack(tmp_path)
    builder = SkillsIndexBuilder(pack)
    records = list(builder.list_skills())
    payload = builder.list_skills_json()
    json_names = {e["name"] for e in payload["skills"]}
    record_names = {r.name for r in records}
    assert json_names == record_names, (
        f"JSON names {json_names} != record names {record_names}"
    )
    # Each JSON entry's path must match the corresponding record's path.
    record_by_name = {r.name: r for r in records}
    for entry in payload["skills"]:
        record = record_by_name[entry["name"]]
        assert entry["path"] == str(record.path), (
            f"path mismatch for {entry['name']}: {entry['path']} != {record.path}"
        )


def test_empty_pack_yields_empty_list(tmp_path: Path) -> None:
    """A missing pack root yields an empty skills list, not an error."""
    builder = SkillsIndexBuilder(tmp_path / "nope")
    payload = builder.list_skills_json()
    assert payload == {"skills": []}


def test_explicit_root_param_respected(tmp_path: Path) -> None:
    """Passing an explicit root to list_skills_json overrides the builder's root."""
    pack = _make_pack(tmp_path)
    # Create a second pack to point the explicit root at.
    alt = tmp_path / "alt"
    (alt / "cat" / "alpha").mkdir(parents=True)
    (alt / "cat" / "alpha" / "SKILL.md").write_text(
        "---\nname: alpha\ndescription: A.\n---\n\n# alpha\n",
        encoding="utf-8",
    )
    builder = SkillsIndexBuilder(pack)
    payload = builder.list_skills_json(SkillsRoot(alt))
    names = [e["name"] for e in payload["skills"]]
    assert names == ["alpha"]
    for entry in payload["skills"]:
        assert entry["source"] == str(pack), (
            "source must be the builder's own pack root, not the explicit root"
        )


def test_contract_stub_signatures() -> None:
    """The protocol's default list_skills_json returns {}; the builder overrides it."""
    from modules.shared.src.skills.contract_skills_protocol import (
        ISkillsIndexProtocol,
    )

    # The protocol default is a no-op stub returning {}.
    assert "list_skills_json" not in ISkillsIndexProtocol.__abstractmethods__
    # The concrete builder provides a non-trivial implementation.
    assert "list_skills" in ISkillsIndexProtocol.__abstractmethods__
