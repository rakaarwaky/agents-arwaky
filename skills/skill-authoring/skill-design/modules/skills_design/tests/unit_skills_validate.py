"""Golden regression tests for the 13-rule validator folded into SkillsLinter."""

from __future__ import annotations

from pathlib import Path

import pytest

from skills_design.src.taxonomy_skills_rule_vo import (
    ISSUE_MESSAGES,
    RULE_IDS,
    RULES,
    IssueType,
    is_valid_skill_name,
    issue_message,
    rule,
)
from skills_design.src.capabilities_skills_linter import SkillsLinter
from skills_design.tests.fixture_skills import as_root, crafted_tree

FIXTURES = Path(__file__).resolve().parent / "fixtures"

# The one crafted tree per issue type, and the locator the report must
# show for it. Mirrors the pack's golden fixture map.
GOLDEN = {
    IssueType.NAME_MISMATCH: "cat-a/good-skill",
    IssueType.INVALID_SKILL_NAME: "cat-a/bad--name",
    IssueType.MISSING_DESCRIPTION: "cat-a/good-skill",
    IssueType.INVALID_DESCRIPTION_CHARACTERS: "cat-a/good-skill",
    IssueType.DESCRIPTION_TOO_LONG: "cat-a/good-skill",
    IssueType.NESTED_SKILL_MD: "cat-a/good-skill",
    IssueType.INVALID_PLACEMENT: "cat-a/SKILL.md",
    IssueType.TOO_DEEP: "cat-a/deep/nest/SKILL.md",
    IssueType.DUPLICATE_SKILL_NAME: "library",
    IssueType.DUPLICATE_DESCRIPTION: "library",
    IssueType.MISSING_CATEGORY_DESCRIPTION: "cat-a",
    IssueType.EMPTY_CATEGORY_DESCRIPTION: "cat-a",
    IssueType.EMPTY_CATEGORY: "cat-a",
}


def test_rule_table_is_the_thirteen_rule_ssot() -> None:
    """13 rules, stable ids, and messages that cannot drift from the table."""
    assert len(RULES) == 13
    assert len(RULE_IDS) == 13
    assert tuple(item.id for item in RULES) == tuple(RULE_IDS)
    for one_rule in RULES:
        assert rule(one_rule.id) is one_rule
        assert one_rule.detail_md == ISSUE_MESSAGES[one_rule.issue]
        assert one_rule.level.value == "error"


def test_issue_message_renders_verbatim_templates() -> None:
    """Templates interpolate the legacy fields exactly."""
    assert issue_message(IssueType.NAME_MISMATCH, name="a", dir="b") == (
        "Frontmatter name 'a' does not match directory 'b'."
    )
    assert issue_message(IssueType.DESCRIPTION_TOO_LONG, length=2000, max_len=1024) == (
        "Description is 2000 chars; max is 1024."
    )


def test_is_valid_skill_name_matches_the_legacy_predicate() -> None:
    """The compound name predicate is unchanged."""
    assert is_valid_skill_name("fetch-mcp")
    assert not is_valid_skill_name("Fetch")
    assert not is_valid_skill_name("a")
    assert not is_valid_skill_name("bad--name")
    assert not is_valid_skill_name("-leading")
    assert not is_valid_skill_name("x" * 65)


@pytest.mark.parametrize("issue_type", list(IssueType))
def test_golden_fixture_per_issue_type(issue_type: IssueType) -> None:
    """Each fixture reports exactly its target issue, message, and locator."""
    fixture_root = FIXTURES / issue_type.value
    assert fixture_root.is_dir(), f"missing golden fixture for {issue_type.value}"

    report = SkillsLinter().lint(as_root(fixture_root))

    assert len(report.unfiltered_issues) == 1, (
        f"{issue_type.value}: expected exactly 1 validator issue, got "
        f"{len(report.unfiltered_issues)}: {report.unfiltered_issues}"
    )

    issue = report.unfiltered_issues[0]
    assert issue.type == issue_type.value
    assert issue.locator == GOLDEN[issue_type]
    assert issue.message == _expected_message(issue, issue_type)


def _expected_message(issue, issue_type: IssueType) -> str:
    """Recompute the message from the template and the fixture's fields."""
    if issue_type is IssueType.NAME_MISMATCH:
        return issue_message(issue_type, name="wrong-name", dir="good-skill")
    if issue_type is IssueType.DESCRIPTION_TOO_LONG:
        return issue_message(issue_type, length=1100, max_len=1024)
    if issue_type is IssueType.NESTED_SKILL_MD:
        return ISSUE_MESSAGES[issue_type].format(paths=issue.message.split(": ", 1)[1])
    if issue_type is IssueType.DUPLICATE_SKILL_NAME:
        return issue_message(
            issue_type, name="good-skill", paths="cat-a/good-skill, cat-b/good-skill"
        )
    if issue_type is IssueType.DUPLICATE_DESCRIPTION:
        return issue_message(
            issue_type, paths="cat-a/alpha-skill, cat-b/beta-skill"
        )
    return ISSUE_MESSAGES[issue_type]


def test_clean_fixture_reports_no_issues() -> None:
    """The clean tree reports zero validator issues and the derived counts."""
    report = SkillsLinter().lint(as_root(FIXTURES / "clean"))
    assert len(report.unfiltered_issues) == 0
    assert report.summary() == "0 issues / 1 skills / 1 categories"


def test_report_is_unfiltered_by_design(tmp_path: Path) -> None:
    """The linter never narrows on its own: filtering is the surface's job."""
    report = SkillsLinter().lint(as_root(crafted_tree(tmp_path)))
    assert len(report.unfiltered_issues) == 1
    assert report.unfiltered_issues[0].type == IssueType.NAME_MISMATCH.value
