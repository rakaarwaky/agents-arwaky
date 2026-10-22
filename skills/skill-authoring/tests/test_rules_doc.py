"""Tests for the generated rules document.

Pins the contract the design doc (§5.3, risk R7) calls for: every
``IssueType`` renders into the markdown, the doc carries all 13 verbatim
message strings (so it cannot disagree with the executable rules), and
``cli rules --markdown`` reproduces the committed artifact byte-for-byte.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import docs
from skill_rules import ISSUE_MESSAGES, RULES, IssueType, rule

PACK_ROOT = Path(__file__).resolve().parent.parent
COMMITTED_DOC = PACK_ROOT / "_rules" / "skill-rules.md"
CLI = PACK_ROOT / "scripts" / "cli.py"
REPO_ROOT = PACK_ROOT.parents[2]


def test_every_issue_type_renders():
    """The doc has one section per rule — 13 rules, 13 rendered sections."""
    rendered = docs.render_rules_markdown()
    for one_rule in RULES:
        assert f"### `{one_rule.id}`" in rendered, f"missing section for {one_rule.id}"
    assert rendered.count("\n### `") == len(list(IssueType))


def test_doc_contains_every_verbatim_message():
    """All 13 message templates appear verbatim — the doc cannot state a
    constraint the checker does not enforce (design risk R7)."""
    rendered = docs.render_rules_markdown()
    for issue_type, template in ISSUE_MESSAGES.items():
        assert f"> {template}" in rendered, f"missing verbatim message for {issue_type.value}"


def test_markdown_is_stable():
    """Byte-stable across calls: the rendered doc depends only on the
    SSOT, so regeneration is a no-op on a clean checkout."""
    assert docs.render_rules_markdown() == docs.render_rules_markdown()


def test_rule_lookup_resolves_every_published_id():
    """``rule(<id>)`` is the lookup the checkers and the docs generator
    read through; it resolves for every id the doc renders."""
    for one_rule in RULES:
        assert rule(one_rule.id) is one_rule
        assert rule(one_rule.id).detail_md == ISSUE_MESSAGES[one_rule.issue]


def test_committed_doc_matches_generator():
    """The committed artifact is exactly what the generator emits — the
    round-trip that makes a CI diff gate on hand edits meaningful."""
    assert COMMITTED_DOC.read_text(encoding="utf-8") == docs.render_rules_markdown()


def test_cli_markdown_matches_committed_artifact():
    """The canonical invocation (design §5.3)::

        python3 skills/skill-authoring/scripts/cli.py rules --markdown

    reproduces the committed file. Run from the repo root, the way the
    PR-7 CI step will, and the way the regeneration command is written.
    """
    completed = subprocess.run(
        [sys.executable, str(CLI), "rules", "--markdown"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == COMMITTED_DOC.read_text(encoding="utf-8")


def test_cli_rules_plain_is_compact_and_lists_every_rule():
    """The plain form prints one line per rule — the summary view."""
    completed = subprocess.run(
        [sys.executable, str(CLI), "rules"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    for one_rule in RULES:
        assert one_rule.id in completed.stdout
        assert one_rule.summary in completed.stdout
