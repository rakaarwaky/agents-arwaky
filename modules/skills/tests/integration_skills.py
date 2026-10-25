"""Integration tests for modules/skills — layers wired together."""

from __future__ import annotations

from pathlib import Path

from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsCatalogProtocol,
)
from modules.shared.src.skills.taxonomy_skills_authoring_vo import (
    CatalogCheckResult,
    CatalogReport,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)
from modules.skills.src.agent_skills_orchestrator import SkillsAgent
from modules.skills.src.capabilities_skills_catalog import SkillsCatalog
from modules.skills.src.capabilities_skills_index_builder import SkillsIndexBuilder
from modules.skills.src.capabilities_skills_mutator import SkillsMutator
from modules.skills.src.capabilities_skills_pack_reader import SkillsPackReader
from modules.skills.src.capabilities_skills_validator import SkillsValidator
from modules.skills.src.root_skills_container import default_aggregate
from modules.skills.tests.fixture_skills import as_root, crafted_tree


def _make_pack(tmp_path: Path) -> Path:
    pack = tmp_path / "skills"
    (pack / "web" / "fetch-mcp").mkdir(parents=True)
    (pack / "web" / "fetch-mcp" / "SKILL.md").write_text(
        "---\nname: fetch-mcp\ndescription: Scrapes web to markdown.\n---\n\n# Fetch\n",
        encoding="utf-8",
    )
    return pack


def test_container_wires_agent_to_capability(tmp_path: Path) -> None:
    """INT-SKILLS-001: the container wires the capability into the agent."""
    aggregate = default_aggregate(index=SkillsIndexBuilder(_make_pack(tmp_path)))
    result = aggregate.execute(SkillsRequest(op="list"))
    assert result.ok
    assert [r.name for r in result.records] == ["fetch-mcp"]


def test_surface_through_container(tmp_path: Path) -> None:
    """INT-SKILLS-002: surface + container resolve a show request."""
    from modules.cli.src.surface_skills_command import cmd_skills

    aggregate = default_aggregate(index=SkillsIndexBuilder(_make_pack(tmp_path)))
    rc = cmd_skills(["show", "fetch-mcp"], aggregate)
    assert rc == 0


class _SpyCatalog(ISkillsCatalogProtocol):
    """Records the agent's mutation→catalog pipeline order."""

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


def test_move_apply_applies_once_then_rebuilds_once(tmp_path: Path) -> None:
    """The agent owns `plan → apply → catalog rebuild`, in that order."""
    root = crafted_tree(tmp_path)
    calls: list[str] = []
    catalog = _SpyCatalog(calls)

    original_apply = SkillsMutator.apply

    def spy_apply(self, plan):  # type: ignore[no-untyped-def]
        calls.append("apply")
        return original_apply(self, plan)

    SkillsMutator.apply = spy_apply
    try:
        agent = SkillsAgent(
            SkillsIndexBuilder(root),
            SkillsPackReader(root),
            catalog=catalog,
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
    finally:
        SkillsMutator.apply = original_apply

    assert result.ok
    assert calls == ["apply", "rebuild"]


def test_move_dry_run_never_applies_or_rebuilds(tmp_path: Path) -> None:
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
    assert calls == []
    assert (root / "drafts" / "doc-drafts").exists()


def test_agent_maps_typed_errors_to_exit_codes(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    agent = SkillsAgent(
        SkillsIndexBuilder(root),
        SkillsPackReader(root),
        catalog=SkillsCatalog(),
        mutator=SkillsMutator(),
        validator=SkillsValidator(),
        default_root=root,
    )

    missing = agent.execute(
        SkillsRequest(
            op=SkillsOp.MOVE,
            query=SkillQuery("nope"),
            root=as_root(root),
            flags={"target": "notes"},
        )
    )
    assert not missing.ok
    assert missing.exit_code == 2
    assert missing.message.startswith("Could not find skill directory")

    bad_root = agent.execute(
        SkillsRequest(op=SkillsOp.VALIDATE, root=as_root(tmp_path / "nope"))
    )
    assert bad_root.exit_code == 2
    assert bad_root.message.startswith("Skills root does not exist")
