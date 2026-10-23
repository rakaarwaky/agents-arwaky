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


def test_assets_container_marker_suppresses_empty_and_missing_description():
    """DM2: a declared ``ASSETS.md`` (frontmatter ``kind: assets`` + a
    one-line purpose) in a category directory suppresses exactly
    ``empty-category`` and ``missing-category-description`` — and only
    when the declaration is present.

    Cover all four combinations:
      - declared assets container (no skills, no DESCRIPTION.md) -> 0
      - stray ``ASSETS.md`` without ``kind: assets`` -> both issues
      - empty category without ``ASSETS.md`` -> both issues
      - declared assets container that also has a skill -> no
        empty-category issue, the marker does not hide skills
    """
    import json
    import shutil
    import tempfile

    def write_skill(root: Path, category: str, skill: str, desc: str) -> None:
        d = root / category / skill
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            f"---\nname: {skill}\ndescription: {json.dumps(desc)}\n---\n",
            encoding="utf-8",
        )

    def declare_assets(root: Path, category: str, purpose: str) -> None:
        (root / category).mkdir(parents=True, exist_ok=True)
        (root / category / "ASSETS.md").write_text(
            f"---\ndescription: {json.dumps(purpose)}\nkind: assets\n---\n\n"
            f"{purpose}\n",
            encoding="utf-8",
        )

    def stray_assets(root: Path, category: str) -> None:
        (root / category / "ASSETS.md").write_text(
            "# Stray file\n\nNo frontmatter declaration.\n", encoding="utf-8"
        )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # 1. Declared assets container, empty: no issues at all.
        declare_assets(root, "shared", "Cross-skill assets.")
        report = validate_library(root)
        assert report["issue_count"] == 0, report["issues"]

        # 2. Stray ASSETS.md without the kind declaration: the marker does
        #    not opt in, both issues stand.
        root2 = Path(tempfile.mkdtemp())
        try:
            (root2 / "shared").mkdir()
            stray_assets(root2, "shared")
            report = validate_library(root2)
            types = sorted(i["type"] for i in report["issues"])
            assert types == ["empty-category", "missing-category-description"], types
        finally:
            shutil.rmtree(root2, ignore_errors=True)

        # 3. No ASSETS.md at all: both issues stand (the standing empty-category
        #    defect).
        root3 = Path(tempfile.mkdtemp())
        try:
            (root3 / "shared").mkdir()
            report = validate_library(root3)
            types = sorted(i["type"] for i in report["issues"])
            assert types == ["empty-category", "missing-category-description"], types
        finally:
            shutil.rmtree(root3, ignore_errors=True)

        # 4. Declared assets container that also holds a skill: the marker
        #    suppresses the two emptiness checks only; the skill row still
        #    validates normally (no name-mismatch here, just no new issues
        #    from the marker).
        write_skill(root, "mixed", "a-skill", "A skill living next to a declared assets container.")
        declare_assets(root, "mixed", "Mixed assets and skills.")
        report = validate_library(root)
        # The mixed category now has a DESCRIPTION-free state but is not empty
        # (it holds a-skill), so neither category-level issue applies; the
        # assets container "shared" is declared, so its two issues are gone.
        assert report["issue_count"] == 0, report["issues"]


def test_nested_pack_marker_exempts_too_deep_files():
    """DM1: an intermediate directory that carries the ``pack.toml``
    marker opts its one-level-deeper ``SKILL.md`` files in — the
    ``too-deep`` error is suppressed for exactly those paths, and only
    when the marker is present.

    Cover both presence and absence paths in one tree:
      - ``cat-a/nested-pack/SKILL.md`` with ``cat-a/nested-pack/pack.toml``
        -> no too-deep issue
      - ``cat-a/loose/SKILL.md`` without a marker -> too-deep issue
        (the marker did not leak to siblings)
    """
    import json
    import tempfile

    def write_skill(root: Path, category: str, skill: str, desc: str) -> None:
        d = root / category / skill
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            f"---\nname: {skill}\ndescription: {json.dumps(desc)}\n---\n",
            encoding="utf-8",
        )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # A category with a DESCRIPTION.md and one top-level skill so
        # only the too-deep defect is in play (empty-category is not).
        (root / "cat-a").mkdir()
        (root / "cat-a" / "DESCRIPTION.md").write_text(
            '---\ndescription: "Cat A"\n---\n', encoding="utf-8"
        )
        top_skill = root / "cat-a" / "top-skill"
        top_skill.mkdir()
        (top_skill / "SKILL.md").write_text(
            "---\nname: top-skill\n"
            f"description: {json.dumps('A top-level skill in cat-a.')}\n"
            "---\n",
            encoding="utf-8",
        )

        # Nested pack (exempt): cat-a/nested-pack/inner-skill/SKILL.md with
        # cat-a/nested-pack/pack.toml present.
        nested_dir = root / "cat-a" / "nested-pack" / "inner-skill"
        nested_dir.mkdir(parents=True)
        (nested_dir / "SKILL.md").write_text(
            "---\nname: inner-skill\n"
            f"description: {json.dumps('An inner skill of a nested pack.')}\n"
            "---\n",
            encoding="utf-8",
        )
        (root / "cat-a" / "nested-pack" / "pack.toml").write_text(
            "# Nested pack marker (DM1): exempts inner SKILL.md files\n"
            "# from the too-deep check.\n",
            encoding="utf-8",
        )

        # Loose (not exempt): cat-a/loose-pack/loose-skill/SKILL.md with no
        # pack.toml next to loose-pack/.
        loose_dir = root / "cat-a" / "loose-pack" / "loose-skill"
        loose_dir.mkdir(parents=True)
        (loose_dir / "SKILL.md").write_text(
            "---\nname: loose-skill\n"
            f"description: {json.dumps('A loose skill without a pack marker.')}\n"
            "---\n",
            encoding="utf-8",
        )

        report = validate_library(root)
        types = sorted(i["type"] for i in report["issues"])
        assert types == ["too-deep"], types
        assert (
            report["issues"][0]["path"] == "cat-a/loose-pack/loose-skill/SKILL.md"
        ), report["issues"]
        # The nested-pack inner skill produced no too-deep issue.
        assert not any(
            i["path"] == "cat-a/nested-pack/inner-skill/SKILL.md"
            for i in report["issues"]
        )


def test_real_tree_validate_zero_issues():
    """After PR-8 the committed real tree validates clean: 0 issues
    library-wide. Runs against the actual ``skills/`` directory at the
    repo root (not a fixture), pinned for G5.
    """
    import subprocess
    import sys

    # Walk up from the test file to the repo root (worktree or main clone).
    test_file = Path(__file__).resolve()
    repo_root = None
    for candidate in test_file.parents:
        if (candidate / ".git").exists():
            repo_root = candidate
            break
    assert repo_root is not None, "no repo root found walking up from the test file"

    completed = subprocess.run(
        [
            sys.executable,
            str(repo_root / "skills" / "skill-authoring" / "scripts" / "cli.py"),
            "validate",
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, (
        f"expected exit 0 (0 issues), got {completed.returncode}:\n"
        f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
    )
    assert "No validation issues found." in completed.stdout, completed.stdout
