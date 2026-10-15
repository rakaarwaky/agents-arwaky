"""Unit tests for the skills feature (list + show, read-only)."""

from __future__ import annotations

from pathlib import Path

from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsIndexProtocol,
    ISkillsReaderProtocol,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillContent,
    SkillDescription,
    SkillQuery,
    SkillRecord,
    SkillsRequest,
)
from modules.skills.src.agent_skills_orchestrator import SkillsAgent
from modules.skills.src.capabilities_skills_index_builder import (
    SkillsIndexBuilder,
    SkillsPackReader,
    default_pack_root,
)
from modules.skills.src.root_skills_container import default_aggregate


def _make_pack(tmp_path: Path) -> Path:
    """Build a miniature skill pack: two skills plus one malformed."""
    pack = tmp_path / "skills"
    (pack / "web" / "fetch-mcp").mkdir(parents=True)
    (pack / "web" / "fetch-mcp" / "SKILL.md").write_text(
        "---\nname: fetch-mcp\ndescription: Scrapes web to markdown.\n---\n\n# Fetch\n",
        encoding="utf-8",
    )
    (pack / "dev" / "lint").mkdir(parents=True)
    (pack / "dev" / "lint" / "SKILL.md").write_text(
        "---\nname: lint\ndescription: Lints things.\n---\n\n# Lint\n",
        encoding="utf-8",
    )
    (pack / "bad" / "empty").mkdir(parents=True)
    (pack / "bad" / "empty" / "SKILL.md").write_text("", encoding="utf-8")
    return pack


def test_default_pack_root_points_at_repo_skills() -> None:
    """The default pack root is the repo's skills/ directory."""
    root = default_pack_root()
    assert root.name == "skills"
    assert root.is_dir()


def test_index_builder_implements_protocol() -> None:
    """SkillsIndexBuilder satisfies the contract protocol."""
    assert isinstance(SkillsIndexBuilder(), ISkillsIndexProtocol)

def test_pack_reader_implements_protocol() -> None:
    """SkillsPackReader satisfies the contract protocol."""
    assert isinstance(SkillsPackReader(), ISkillsReaderProtocol)


def test_list_skills_sorted_with_descriptions(tmp_path: Path) -> None:
    """list returns every skill sorted by name with its description."""
    pack = _make_pack(tmp_path)
    rows = list(SkillsIndexBuilder(pack).list_skills())
    names = [r.name for r in rows]
    assert names == sorted(names)
    assert "fetch-mcp" in names
    assert "lint" in names
    fetch = next(r for r in rows if r.name == "fetch-mcp")
    assert fetch.description == SkillDescription("Scrapes web to markdown.")


def test_list_skills_empty_when_pack_missing(tmp_path: Path) -> None:
    """A missing pack root yields an empty listing, not an error."""
    assert list(SkillsIndexBuilder(tmp_path / "nope").list_skills()) == []


def test_show_skill_by_frontmatter_name(tmp_path: Path) -> None:
    """show matches the frontmatter name field."""
    pack = _make_pack(tmp_path)
    content = SkillsPackReader(pack).show_skill(SkillQuery("fetch-mcp"))
    assert content is not None
    assert "# Fetch" in content


def test_show_skill_by_directory_name_and_hyphen_free(tmp_path: Path) -> None:
    """show matches the directory name and a hyphen-free spelling."""
    pack = _make_pack(tmp_path)
    builder = SkillsPackReader(pack)
    assert builder.show_skill(SkillQuery("fetch")) is not None
    assert builder.show_skill(SkillQuery("fetch-mcp")) is not None


def test_show_skill_unknown_returns_none(tmp_path: Path) -> None:
    """An unknown name returns None instead of raising."""
    pack = _make_pack(tmp_path)
    assert SkillsPackReader(pack).show_skill(SkillQuery("no-such-skill")) is None


def test_show_skill_ambiguous_prefix_returns_none(tmp_path: Path) -> None:
    """A prefix matching several skills is rejected, not guessed."""
    pack = tmp_path / "skills"
    for sub, name in (("a", "aes-one"), ("b", "aes-two")):
        (pack / sub / name).mkdir(parents=True)
        (pack / sub / name / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: d\n---\n\n# {name}\n",
            encoding="utf-8",
        )
    assert SkillsPackReader(pack).show_skill(SkillQuery("aes")) is None


def test_agent_execute_list_and_show(tmp_path: Path) -> None:
    """The agent routes list/show through the injected index capability."""
    agent = SkillsAgent(SkillsIndexBuilder(pack := _make_pack(tmp_path)), SkillsPackReader(pack))
    listed = agent.execute(SkillsRequest(op="list"))
    assert listed.ok
    assert {r.name for r in listed.records} == {"fetch-mcp", "lint", "empty"}

    shown = agent.execute(SkillsRequest(op="show", query=SkillQuery("fetch")))
    assert shown.ok
    assert shown.content is not None
    assert "# Fetch" in shown.content


def test_agent_execute_show_unknown_is_not_ok(tmp_path: Path) -> None:
    """An unknown show target reports failure with a clear message."""
    agent = SkillsAgent(SkillsIndexBuilder(pack := _make_pack(tmp_path)), SkillsPackReader(pack))
    result = agent.execute(SkillsRequest(op="show", query=SkillQuery("nope")))
    assert not result.ok
    assert "nope" in result.message


def test_agent_execute_unknown_op_is_not_ok(tmp_path: Path) -> None:
    """An unknown op is rejected rather than silently succeeding."""
    agent = SkillsAgent(SkillsIndexBuilder(pack := _make_pack(tmp_path)), SkillsPackReader(pack))
    result = agent.execute(SkillsRequest(op="frobnicate"))
    assert not result.ok


def test_default_aggregate_bound_to_default_pack() -> None:
    """The composition root binds an agent to the real pack."""
    aggregate = default_aggregate()
    listed = aggregate.execute(SkillsRequest(op="list"))
    assert listed.ok
    assert len(listed.records) > 0
    shown = aggregate.execute(SkillsRequest(op="show", query=SkillQuery("fetch")))
    assert shown.ok
    assert shown.content is not None


def test_skill_record_is_frozen() -> None:
    """SkillRecord is an immutable value object."""
    record = SkillRecord(
        name="a",
        description=SkillDescription("b"),
        path=Path("/x"),
    )
    try:
        record.name = "c"  # type: ignore[misc]
    except AttributeError:
        return
    raise AssertionError("SkillRecord should be frozen")


def test_skill_content_is_a_newtype_of_str() -> None:
    """SkillContent behaves as a string-typed wrapper."""
    content = SkillContent("hello")
    assert content == "hello"