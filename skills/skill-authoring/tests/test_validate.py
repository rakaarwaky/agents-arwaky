"""Golden regression tests for the 13 issue types.

One crafted fixture tree per issue type lives under
``fixtures/<issue-type>/``; each test asserts the validator reports
exactly one issue, of the right type, with the right verbatim message.
The whole suite is the golden pin the design doc's risk R3 calls for:
any message or ordering drift in ``validate.py`` or ``librarian.py``
fails here.
"""

from __future__ import annotations

from pathlib import Path

import skill_rules
from skill_rules import IssueType, issue_message
from validate import validate_library

FIXTURES = Path(__file__).resolve().parent / "fixtures"

# The one crafted tree per issue type, and the locator the report must
# show for it.
GOLDEN: dict[IssueType, str] = {
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


def test_golden_fixture_per_issue_type():
    """Every IssueType has a golden fixture, and each fixture tree reports
    exactly one issue: the target type, with the target message."""
    for issue_type in IssueType:
        fixture_root = FIXTURES / issue_type.value
        assert fixture_root.is_dir(), f"missing golden fixture for {issue_type.value}"

        report = validate_library(fixture_root)

        assert report["issue_count"] == 1, (
            f"{issue_type.value}: expected exactly 1 issue, got "
            f"{report['issue_count']}: {report['issues']}"
        )

        issue = report["issues"][0]
        assert issue["type"] == issue_type.value, (
            f"{issue_type.value}: got issue type {issue['type']!r}"
        )

        expected_locator = GOLDEN[issue_type]
        locator = issue.get("path") or issue.get("category") or "library"
        assert locator == expected_locator, (
            f"{issue_type.value}: expected locator {expected_locator!r}, "
            f"got {locator!r}"
        )

        # The message must be the verbatim SSOT template rendered with the
        # same fields the original callsite used.
        assert issue["message"] == expected_message_for(issue, issue_type)


def expected_message_for(issue: dict, issue_type: IssueType) -> str:
    """Recompute the expected message from the SSOT template + issue fields.

    Mirrors the original ``librarian.py`` callsite shape field-for-field,
    so any template drift in ``skill_rules.ISSUE_MESSAGES`` fails here.
    """
    if issue_type is IssueType.NAME_MISMATCH:
        return issue_message(
            issue_type, name="wrong-name", dir="good-skill"
        )
    if issue_type is IssueType.INVALID_SKILL_NAME:
        return issue_message(issue_type)
    if issue_type is IssueType.MISSING_DESCRIPTION:
        return issue_message(issue_type)
    if issue_type is IssueType.INVALID_DESCRIPTION_CHARACTERS:
        return issue_message(issue_type)
    if issue_type is IssueType.DESCRIPTION_TOO_LONG:
        return issue_message(issue_type, length=1100, max_len=skill_rules.MAX_DESCRIPTION_LEN)
    if issue_type is IssueType.NESTED_SKILL_MD:
        return issue_message(issue_type, paths="cat-a/good-skill/references/inner/SKILL.md")
    if issue_type is IssueType.INVALID_PLACEMENT:
        return issue_message(issue_type)
    if issue_type is IssueType.TOO_DEEP:
        return issue_message(issue_type)
    if issue_type is IssueType.DUPLICATE_SKILL_NAME:
        return issue_message(
            issue_type, name="good-skill",
            paths="cat-a/good-skill, cat-b/good-skill",
        )
    if issue_type is IssueType.DUPLICATE_DESCRIPTION:
        return issue_message(
            issue_type,
            paths="cat-a/alpha-skill, cat-b/beta-skill",
        )
    if issue_type is IssueType.MISSING_CATEGORY_DESCRIPTION:
        return issue_message(issue_type)
    if issue_type is IssueType.EMPTY_CATEGORY_DESCRIPTION:
        return issue_message(issue_type)
    if issue_type is IssueType.EMPTY_CATEGORY:
        return issue_message(issue_type)
    raise AssertionError(f"unhandled issue type {issue_type}")


def test_issue_type_values_are_stable():
    """The 13 strings the validator emits are pinned here: a rename or
    rephrase of an issue type breaks every downstream consumer, so the
    values themselves are part of the golden contract."""
    expected = [
        "name-mismatch",
        "invalid-skill-name",
        "missing-description",
        "invalid-description-characters",
        "description-too-long",
        "nested-skill-md",
        "invalid-placement",
        "too-deep",
        "duplicate-skill-name",
        "duplicate-description",
        "missing-category-description",
        "empty-category-description",
        "empty-category",
    ]
    assert sorted(t.value for t in IssueType) == sorted(expected)
    assert len(list(IssueType)) == 13


def test_clean_fixture_reports_no_issues():
    """A fully valid tree reports zero issues — the control that keeps the
    golden fixtures from passing vacuously."""
    import json

    # Reuse the same layout the fixtures use, but fully valid: one
    # category with DESCRIPTION.md and one skill with matching name and
    # a clean description.
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        cat = Path(tmp) / "cat-a"
        skill = cat / "good-skill"
        skill.mkdir(parents=True)
        (cat / "DESCRIPTION.md").write_text('---\ndescription: "Test category a"\n---\n')
        (skill / "SKILL.md").write_text(
            "---\nname: good-skill\n"
            f"description: {json.dumps('A clearly scoped skill description that is unique enough to never collide.')}\n"
            "---\n\n# good-skill\n",
            encoding="utf-8",
        )

        report = validate_library(Path(tmp))
        assert report["issue_count"] == 0, report["issues"]


def test_assets_container_marker_suppresses_category_shape_issues():
    """DM2: a directory declaring ``kind: assets`` in ``ASSETS.md`` is exempt
    from ``missing-category-description`` and ``empty-category``; a marker
    without the declaration is not (R8 — a real category cannot opt out)."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        assets = Path(tmp) / "shared"
        assets.mkdir()
        (assets / "ASSETS.md").write_text(
            "---\ndescription: Cross-skill shared assets.\nkind: assets\n---\n",
            encoding="utf-8",
        )

        report = validate_library(Path(tmp))
        assert report["issue_count"] == 0, report["issues"]

    with tempfile.TemporaryDirectory() as tmp:
        # Marker present but not declared (no kind: assets) — not an
        # asset container, so both category-shape issues still fire.
        assets = Path(tmp) / "shared"
        assets.mkdir()
        (assets / "ASSETS.md").write_text(
            "---\ndescription: A real category.\n---\n",
            encoding="utf-8",
        )

        report = validate_library(Path(tmp))
        types = {i["type"] for i in report["issues"]}
        assert types == {
            "missing-category-description",
            "empty-category",
        }, report["issues"]


def test_nested_pack_marker_exempts_too_deep_files():
    """DM1: a ``pack.toml`` marker in a category exempts its one-level-deeper
    ``SKILL.md`` files from ``too-deep``; without the marker they still fail."""
    import json
    import tempfile

    def build(root: Path, with_marker: bool) -> None:
        # Mirrors the real layout: category/pack-dir/sub-skill/SKILL.md
        # (4 components, one deeper than category/skill/SKILL.md), plus a
        # plain sibling skill so the category itself is non-empty.
        cat = root / "cat-a"
        pack = cat / "pack-root"
        skill_md = pack / "orca-cli" / "SKILL.md"
        skill_md.parent.mkdir(parents=True)
        skill_md.write_text(
            "---\nname: orca-cli\n"
            f"description: {json.dumps('Operate an orca worktree.')}\n"
            "---\n\n# orca-cli\n",
            encoding="utf-8",
        )
        sibling = cat / "good-skill" / "SKILL.md"
        sibling.parent.mkdir(parents=True)
        sibling.write_text(
            "---\nname: good-skill\n"
            f"description: {json.dumps('A clearly scoped skill description that is unique enough to never collide.')}\n"
            "---\n\n# good-skill\n",
            encoding="utf-8",
        )
        (cat / "DESCRIPTION.md").write_text(
            "---\ndescription: A category that is a pack root.\n---\n",
            encoding="utf-8",
        )
        if with_marker:
            (pack / "pack.toml").write_text(
                "# nested pack marker\n", encoding="utf-8"
            )

    with tempfile.TemporaryDirectory() as tmp:
        build(Path(tmp), with_marker=True)
        report = validate_library(Path(tmp))
        assert report["issue_count"] == 0, report["issues"]

    with tempfile.TemporaryDirectory() as tmp:
        build(Path(tmp), with_marker=False)
        report = validate_library(Path(tmp))
        too_deep = [i for i in report["issues"] if i["type"] == "too-deep"]
        assert len(too_deep) == 1, report["issues"]
        assert too_deep[0]["path"] == "cat-a/pack-root/orca-cli/SKILL.md"


def test_real_library_reports_zero_issues():
    """End-to-end: the committed library tree validates clean (PR-8's target)."""
    skills_root = Path(__file__).resolve().parents[2]
    report = validate_library(skills_root)
    assert report["issue_count"] == 0, report["issues"]
