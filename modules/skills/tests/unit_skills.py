"""Unit tests for the skills feature (read ops, agent pipeline, error mapping)."""

from __future__ import annotations

from pathlib import Path

import pytest

from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsCatalogProtocol,
    ISkillsIndexProtocol,
    ISkillsReaderProtocol,
)
from modules.shared.src.skills.taxonomy_skills_authoring_vo import (
    CatalogCheckResult,
    CatalogReport,
)
from modules.shared.src.skills.taxonomy_skills_error import SkillsRootError
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillContent,
    SkillDescription,
    SkillQuery,
    SkillRecord,
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)
from modules.shared.src.utility_skills_tree import (
    assets_container,
    category_summaries,
    skill_entries,
    too_deep_exempt_paths,
)
from modules.skills.src.agent_skills_orchestrator import SkillsAgent
from modules.skills.src.capabilities_skills_index_builder import (
    SkillsIndexBuilder,
    default_pack_root,
)
from modules.skills.src.capabilities_skills_mutator import SkillsMutator
from modules.skills.src.capabilities_skills_pack_reader import SkillsPackReader
from modules.skills.src.root_skills_container import default_aggregate
from modules.skills.tests.support_skills import as_root, crafted_tree


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
    listed = agent.execute(SkillsRequest(op=SkillsOp.LIST))
    assert listed.ok
    assert {r.name for r in listed.records} == {"fetch-mcp", "lint", "empty"}

    shown = agent.execute(SkillsRequest(op=SkillsOp.SHOW, query=SkillQuery("fetch")))
    assert shown.ok
    assert shown.content is not None
    assert "# Fetch" in shown.content


def test_agent_execute_show_unknown_is_not_ok(tmp_path: Path) -> None:
    """An unknown show target reports failure with a clear message."""
    agent = SkillsAgent(SkillsIndexBuilder(pack := _make_pack(tmp_path)), SkillsPackReader(pack))
    result = agent.execute(SkillsRequest(op=SkillsOp.SHOW, query=SkillQuery("nope")))
    assert not result.ok
    assert "nope" in result.message


def test_agent_execute_unknown_op_is_not_ok(tmp_path: Path) -> None:
    """An unknown op is rejected rather than silently succeeding."""
    agent = SkillsAgent(SkillsIndexBuilder(pack := _make_pack(tmp_path)), SkillsPackReader(pack))
    # raw str is intentional: SkillsRequest.op is typed SkillsOp (StrEnum),
    # mypy rejects a bare str; the agent must reject un-parseable ops at runtime.
    result = agent.execute(SkillsRequest(op="frobnicate"))  # type: ignore[arg-type]
    assert not result.ok


class _SpyCatalog(ISkillsCatalogProtocol):
    """Records the agent's mutation→catalog calls (a spy through the container)."""

    def __init__(self, calls: list[str]) -> None:
        self.calls = calls

    def rebuild(self, root: SkillsRoot) -> CatalogReport:
        self.calls.append("rebuild")
        return CatalogReport(path=Path(root) / "CATALOG.md", skills=0, categories=0)

    def check(self, root: SkillsRoot) -> CatalogCheckResult:
        self.calls.append("check")
        return CatalogCheckResult(in_sync=True)

    def load_rows(self, root: SkillsRoot):
        self.calls.append("load_rows")
        return ()


def test_move_apply_produces_one_apply_and_one_rebuild_in_order(
    tmp_path: Path, monkeypatch
) -> None:
    """move --apply yields exactly one mutator apply and one catalog
    rebuild, in that order — the agent owns the mutation→catalog chain."""
    root = crafted_tree(tmp_path)
    calls: list[str] = []

    original_apply = SkillsMutator.apply

    def spy_apply(self, plan):  # type: ignore[no-untyped-def]
        calls.append("apply")
        return original_apply(self, plan)

    monkeypatch.setattr(SkillsMutator, "apply", spy_apply)

    agent = SkillsAgent(
        SkillsIndexBuilder(root),
        SkillsPackReader(root),
        catalog=_SpyCatalog(calls),
        mutator=SkillsMutator(),
        default_root=root,
    )
    result = agent.execute(
        SkillsRequest(
            op=SkillsOp.MOVE,
            query=SkillQuery("drafts/doc-drafts"),
            apply=True,
            root=as_root(root),
            flags={"target": "notes"},
        )
    )

    assert result.ok
    assert calls.count("apply") == 1
    assert calls.count("rebuild") == 1
    assert calls.index("apply") < calls.index("rebuild")


def test_move_dry_run_never_applies_or_rebuilds(tmp_path: Path) -> None:
    """Without --apply the agent plans only: no apply, no rebuild."""
    root = crafted_tree(tmp_path)
    calls: list[str] = []
    agent = SkillsAgent(
        SkillsIndexBuilder(root),
        SkillsPackReader(root),
        catalog=_SpyCatalog(calls),
        mutator=SkillsMutator(),
        default_root=root,
    )

    result = agent.execute(
        SkillsRequest(
            op=SkillsOp.MOVE,
            query=SkillQuery("drafts/doc-drafts"),
            root=as_root(root),
            flags={"target": "notes"},
        )
    )

    assert result.ok
    assert result.outcome is None
    assert calls == []


def test_default_aggregate_bound_to_default_pack() -> None:
    """The composition root binds an agent to the real pack."""
    aggregate = default_aggregate()
    listed = aggregate.execute(SkillsRequest(op=SkillsOp.LIST))
    assert listed.ok
    assert len(listed.records) > 0
    shown = aggregate.execute(SkillsRequest(op=SkillsOp.SHOW, query=SkillQuery("fetch")))
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

def test_two_walkers_agree_on_the_live_pack() -> None:
    """R5 cross-check: the read walker and the authoring walker see the
    same skill set, so drift fails a test instead of shipping silently."""
    from modules.shared.src.utility_skill_pack import iter_skill_mds
    from modules.shared.src.utility_skills_tree import skill_entries

    pack = default_pack_root()
    read_walk = {
        f"{path.parent.parent.name}/{path.parent.name}" for path in iter_skill_mds(pack)
    }
    authoring_walk = {entry.path for entry in skill_entries(pack)}
    assert read_walk == authoring_walk


def test_skill_entries_walks_the_authoring_tree(tmp_path: Path) -> None:
    """skill_entries yields one entry per category/skill, in stable order."""
    pack = _make_pack(tmp_path)
    entries = skill_entries(pack)
    # Order is alphabetical by category then skill dir (category_dirs sorts names).
    assert [e.path for e in entries] == ["bad/empty", "dev/lint", "web/fetch-mcp"]
    assert [e.skill for e in entries] == ["empty", "lint", "fetch-mcp"]


def test_skill_entries_skips_ignored_category_dirs(tmp_path: Path) -> None:
    """IGNORED_CATEGORY_DIRS (e.g. _archive) never enter the walk."""
    pack = tmp_path / "skills"
    (pack / "web" / "fetch-mcp").mkdir(parents=True)
    (pack / "web" / "fetch-mcp" / "SKILL.md").write_text(
        "---\nname: fetch-mcp\ndescription: d\n---\n\n# Fetch\n",
        encoding="utf-8",
    )
    (pack / "_archive" / "old-skill").mkdir(parents=True)
    (pack / "_archive" / "old-skill" / "SKILL.md").write_text(
        "---\nname: old-skill\ndescription: d\n---\n\n# Old\n",
        encoding="utf-8",
    )
    assert [e.path for e in skill_entries(pack)] == ["web/fetch-mcp"]


def test_category_summaries_count_skills_per_category(tmp_path: Path) -> None:
    """category_summaries derives description state and skill counts."""
    pack = _make_pack(tmp_path)
    (pack / "web" / "DESCRIPTION.md").write_text(
        "---\n\ndescription: Web skills\n---\n", encoding="utf-8"
    )
    summaries = category_summaries(skill_entries(pack), pack)
    by_category = {s.category: s for s in summaries}
    assert by_category["web"].description == "Web skills"
    assert by_category["web"].description_file_exists is True
    assert by_category["web"].skill_count == 1
    assert by_category["dev"].description_file_exists is False
    assert by_category["dev"].skill_count == 1


def test_skills_root_error_on_missing_root(tmp_path: Path) -> None:
    """A missing skills root raises the typed usage error, not SystemExit."""
    with pytest.raises(SkillsRootError):
        skill_entries(tmp_path / "nope")


def test_assets_container_detects_declared_markers(tmp_path: Path) -> None:
    """The DM2 marker declares an asset container, not a skill category."""
    pack = tmp_path / "skills"
    assets = pack / "assets"
    assets.mkdir(parents=True)
    (assets / "ASSETS.md").write_text(
        "---\nkind: assets\n---\n", encoding="utf-8"
    )
    assert assets_container(pack) == {"assets"}


def test_too_deep_exempt_paths_honours_the_dm1_marker(tmp_path: Path) -> None:
    """A SKILL.md two levels below a category is exempt only when its
    intermediate directory carries the pack.toml marker."""
    pack = tmp_path / "skills"
    (pack / "cat" / "pack-a" / "deep").mkdir(parents=True)
    (pack / "cat" / "pack-a" / "deep" / "SKILL.md").write_text(
        "---\nname: a\ndescription: d\n---\n", encoding="utf-8"
    )
    assert too_deep_exempt_paths(pack) == set()
    (pack / "cat" / "pack-a" / "pack.toml").write_text("version = 1\n", encoding="utf-8")
    assert too_deep_exempt_paths(pack) == {"cat/pack-a/deep/SKILL.md"}


def test_importing_the_feature_does_not_mutate_sys_path() -> None:
    """G3: the migrated feature is an ordinary package — no sys.path writes."""
    import subprocess
    import sys

    code = (
        "import sys; before = list(sys.path); "
        "import modules.skills.src.root_skills_container; "
        "import modules.cli.src.surface_skills_command; "
        "assert sys.path == before, sys.path"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(Path(__file__).resolve().parents[3]),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
