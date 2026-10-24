"""Rules-renderer tests, including the committed-artifact round trip."""

from __future__ import annotations

from pathlib import Path

from modules.shared.src.skills.taxonomy_skills_constant import (
    ISSUE_MESSAGES,
    RULES,
    IssueType,
)
from modules.skills.src.capabilities_skills_rules_renderer import SkillsRulesRenderer

PACK_ROOT = Path(__file__).resolve().parents[3] / "skills" / "skill-authoring"
COMMITTED_DOC = PACK_ROOT / "_rules" / "skill-rules.md"


def test_every_rule_renders_one_section() -> None:
    """13 rules → 13 ``###`` sections, each naming its id."""
    document = SkillsRulesRenderer().render_markdown()
    for one_rule in RULES:
        assert f"### `{one_rule.id}`" in document.markdown
    assert document.markdown.count("\n### `") == len(list(IssueType))
    assert document.rule_count == 13


def test_document_contains_every_verbatim_message() -> None:
    """The doc cannot state a constraint the checker does not enforce."""
    document = SkillsRulesRenderer().render_markdown()
    for issue_type, template in ISSUE_MESSAGES.items():
        assert f"> {template}" in document.markdown, issue_type.value


def test_render_is_byte_stable() -> None:
    renderer = SkillsRulesRenderer()
    assert renderer.render_markdown().markdown == renderer.render_markdown().markdown


def test_committed_artifact_matches_the_generator() -> None:
    """``aa skills rules --markdown`` reproduces the committed file exactly."""
    rendered = SkillsRulesRenderer().render_markdown().markdown
    assert COMMITTED_DOC.read_text(encoding="utf-8") == rendered


def test_summary_keeps_the_legacy_first_line() -> None:
    """The compact report is byte-identical to the ported script's."""
    summary = SkillsRulesRenderer().render_summary()
    assert summary.startswith("13 rules from _rules/skill_rules.py:\n")
    assert summary.count("\n- [error]") == 13
