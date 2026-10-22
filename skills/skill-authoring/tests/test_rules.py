"""Tests for the SSOT rules module.

Pins the constants that came out of ``librarian.py`` and the
``Rule``/``IssueType`` taxonomy so PR-3's ``cli rules --markdown``
renderer has a stable contract to build against.
"""

from __future__ import annotations

from skill_rules import (
    CATEGORY_DESCRIPTION_FILENAME,
    IGNORED_CATEGORY_DIRS,
    ISSUE_MESSAGES,
    MAX_DESCRIPTION_LEN,
    NAME_MAX,
    NAME_MIN,
    NAME_RE,
    RULES,
    IssueType,
    Rule,
    clean_one_line,
    is_valid_skill_name,
    issue_message,
    md_escape,
)


def test_name_re_pattern_is_verbatim():
    """The regex is lifted verbatim from librarian.py line 36; pin the
    source string so a silent edit is caught."""
    assert NAME_RE.pattern == r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"


def test_budgets_are_verbatim():
    assert MAX_DESCRIPTION_LEN == 1024
    assert NAME_MIN == 2
    assert NAME_MAX == 64
    assert CATEGORY_DESCRIPTION_FILENAME == "DESCRIPTION.md"


def test_ignored_dirs_match_librarian():
    assert set(IGNORED_CATEGORY_DIRS) == {".git", ".hg", ".svn", "__pycache__", "_archive"}


def test_is_valid_skill_name_predicate():
    assert is_valid_skill_name("good-name")
    assert is_valid_skill_name("a1")
    assert not is_valid_skill_name("-leading")
    assert not is_valid_skill_name("trailing-")
    assert not is_valid_skill_name("double--hyphen")
    assert not is_valid_skill_name("a")  # too short
    assert not is_valid_skill_name("x" * 65)  # too long
    assert not is_valid_skill_name("UPPER")


def test_issue_type_has_exactly_thirteen_values():
    assert len(list(IssueType)) == 13
    assert set(IssueType) == {
        IssueType.NAME_MISMATCH,
        IssueType.INVALID_SKILL_NAME,
        IssueType.MISSING_DESCRIPTION,
        IssueType.INVALID_DESCRIPTION_CHARACTERS,
        IssueType.DESCRIPTION_TOO_LONG,
        IssueType.NESTED_SKILL_MD,
        IssueType.INVALID_PLACEMENT,
        IssueType.TOO_DEEP,
        IssueType.DUPLICATE_SKILL_NAME,
        IssueType.DUPLICATE_DESCRIPTION,
        IssueType.MISSING_CATEGORY_DESCRIPTION,
        IssueType.EMPTY_CATEGORY_DESCRIPTION,
        IssueType.EMPTY_CATEGORY,
    }


def test_issue_messages_have_templates_for_every_type():
    for issue_type in IssueType:
        assert issue_type in ISSUE_MESSAGES, f"no template for {issue_type}"
        assert isinstance(ISSUE_MESSAGES[issue_type], str)


def test_rules_covers_every_issue_type():
    """Every IssueType has exactly one Rule; the Rule's message template
    matches the ISSUE_MESSAGES entry (the two maps must never diverge)."""
    assert len(RULES) == 13
    for rule in RULES:
        assert isinstance(rule, Rule)
        assert rule.message == ISSUE_MESSAGES[rule.issue]
        assert rule.check == rule.issue.value.replace("-", " ")

    assert {r.issue for r in RULES} == set(IssueType)


def test_issue_message_renders_verbatim_templates():
    """The render must produce the exact strings the old librarian.py
    f-strings produced, for the callsite shapes that exist."""
    assert issue_message(IssueType.INVALID_SKILL_NAME) == (
        "Directory name must be lowercase a-z, 0-9, hyphens, 2-64 chars, "
        "no leading/trailing hyphen or double hyphen."
    )
    assert issue_message(
        IssueType.NAME_MISMATCH, name="wrong-name", dir="good-skill"
    ) == "Frontmatter name 'wrong-name' does not match directory 'good-skill'."
    assert issue_message(IssueType.MISSING_DESCRIPTION) == "SKILL.md description is missing."
    assert issue_message(IssueType.INVALID_DESCRIPTION_CHARACTERS) == (
        "Description contains <, >, or double quote characters."
    )
    assert issue_message(
        IssueType.DESCRIPTION_TOO_LONG, length=1242, max_len=MAX_DESCRIPTION_LEN
    ) == "Description is 1242 chars; max is 1024."
    assert issue_message(IssueType.NESTED_SKILL_MD, paths="a/b/SKILL.md") == (
        "Nested SKILL.md files found: a/b/SKILL.md"
    )
    assert issue_message(IssueType.INVALID_PLACEMENT) == (
        "SKILL.md is directly under a category; expected category/skill/SKILL.md."
    )
    assert issue_message(IssueType.TOO_DEEP) == (
        "SKILL.md is nested deeper than category/skill/SKILL.md."
    )
    assert issue_message(
        IssueType.DUPLICATE_SKILL_NAME, name="x", paths="a/x, b/x"
    ) == "Skill name 'x' appears in: a/x, b/x."
    assert issue_message(
        IssueType.DUPLICATE_DESCRIPTION, paths="a/s, b/t"
    ) == "Identical description appears in: a/s, b/t."
    assert issue_message(IssueType.MISSING_CATEGORY_DESCRIPTION) == "DESCRIPTION.md is missing."
    assert issue_message(IssueType.EMPTY_CATEGORY_DESCRIPTION) == "DESCRIPTION.md has no description."
    assert issue_message(IssueType.EMPTY_CATEGORY) == "Category has no skills."


def test_issue_message_missing_field_raises():
    """A callsite that forgets a field must not silently produce a
    malformed message — str.format raises KeyError on the missing name."""
    import pytest

    with pytest.raises(KeyError):
        issue_message(IssueType.NAME_MISMATCH)


def test_escape_helpers_are_verbatim():
    assert clean_one_line("  a   b\n\nc  ") == "a b c"
    assert clean_one_line("") == ""
    assert md_escape("a|b\nc") == "a&#124;b c"
    assert md_escape("|") == "&#124;"
    assert md_escape("x") == "x"
