"""JSONL ledger reader / writer and the post-run invariant engine.

Stdlib only. The ledger JSONL schema is defined in SKILL.md Step 6; this
module adds typed access and the shared ``verify_ledger_invariants`` engine
behind ``validate.py`` checks 1-4.

All new files begin with ``from __future__ import annotations`` so the
``TypedDict`` / ``NamedTuple`` annotations are ``mypy --strict``-clean.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, NamedTuple, TypedDict


class Proof(TypedDict):
    """The ``proof`` object in a ledger entry."""

    verdict: str
    evidence: str


class LedgerEntry(TypedDict):
    """One JSONL ledger row (SKILL.md Step 6 schema).

    ``class`` is a Python keyword; the field is named ``class_`` here and
    mapped to the JSON key ``class``.
    """

    run: str
    row: str
    doc: str
    feature: str
    fr: list[str]
    state: str
    priority: str
    class_: str
    proof: Proof
    closing_condition: str
    issue: int
    action: str


class InvariantViolation(NamedTuple):
    """A single violation found by the invariant engine.

    ``field`` is the ledger field (or ``ledger`` / ``--gh`` when the check
    is on the ledger line itself or the network liveness check); ``message``
    is a human-readable explanation; ``row_id`` identifies the row.
    """

    field: str
    message: str
    row_id: str


# The fixed ``class`` vocabulary (SKILL.md classification table + ledger
# step).  validate.py check 1 asserts every ledger row's class is in here.
CLASS_VOCABULARY: frozenset[str] = frozenset(
    {
        "incomplete",
        "doc_sync",
        "unverified",
        "fr_orphan",
        "skip",
        "skip_next_action",
        "next_action_complete",
        "next_action_pending",
    }
)

# The fixed ``action`` vocabulary (SKILL.md ledger step).
ACTION_VOCABULARY: frozenset[str] = frozenset(
    {"created", "commented", "skipped-exists", "skipped-evidence"}
)

# Rows whose class requires an ``issue`` number in the ledger (check 4):
# every actionable verdict must map to an issue (created, commented, or
# pre-existing).
_ISSUE_REQUIRED_CLASSES: frozenset[str] = frozenset(
    {"incomplete", "doc_sync", "unverified", "fr_orphan"}
)

# Closing-condition shapes (check 2):
# - code-implementation verdicts: the check string must name a
#   ``<feature>/src/`` or ``<feature>/tests/`` path AND a test command.
# - doc-edit verdicts: the source-code path requirement is waived — the
#   check IS the document edit.  ``doc_sync`` / ``next_action_complete``
#   must name the ``<source_doc>`` path and the cell/value; ``fr_orphan``
#   must name the feature's ``BACKLOG.md`` path and the new row.
_CC_CODE_CLASSES: frozenset[str] = frozenset(
    {"incomplete", "unverified", "next_action_pending", "rollup_mismatch"}
)
_CC_DOC_EDIT_CLASSES: frozenset[str] = frozenset(
    {"doc_sync", "next_action_complete", "fr_orphan"}
)


def log(msg: str) -> None:
    """Emit an observability line to stderr with the script prefix."""
    print(f"[task-tracker:ledger] {msg}", file=sys.stderr)


def parse_line(line: str) -> LedgerEntry:
    """Parse one JSONL line into a typed ``LedgerEntry``.

    The JSON key ``class`` is mapped to the ``class_`` field.  Missing
    optional fields (``fr``, ``priority``, ``issue``) are filled with
    defaults so a half-formed line still parses and the invariant engine
    can report exactly which field is wrong instead of crashing here.
    Raises ``json.JSONDecodeError`` on unparseable JSON — callers that
    need to tolerate a bad line should catch it.
    """
    obj: dict[str, Any] = json.loads(line)
    entry: LedgerEntry = {
        "run": str(obj.get("run", "")),
        "row": str(obj.get("row", "")),
        "doc": str(obj.get("doc", "")),
        "feature": str(obj.get("feature", "")),
        "fr": [str(f) for f in (obj.get("fr") or [])],
        "state": str(obj.get("state", "")),
        "priority": str(obj.get("priority", "")),
        "class_": str(obj.get("class", "")),
        "proof": {
            "verdict": str((obj.get("proof") or {}).get("verdict", "")),
            "evidence": str((obj.get("proof") or {}).get("evidence", "")),
        },
        "closing_condition": str(obj.get("closing_condition", "")),
        "issue": int(obj.get("issue", 0) or 0),
        "action": str(obj.get("action", "")),
    }
    return entry


def read_ledger(path: Path) -> list[LedgerEntry]:
    """Read every JSONL line in ``path`` into typed ``LedgerEntry`` objects.

    A malformed line is a *ledger-shape* violation, not a crash: use
    ``read_ledger_lines`` plus check 1 to surface it.  This function
    raises on JSON so ``read_ledger_lines`` is the path that tolerates a
    broken line.
    """
    entries: list[LedgerEntry] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        entries.append(parse_line(line))
    return entries


def read_ledger_lines(path: Path) -> list[str]:
    """Return the non-empty JSONL lines verbatim.

    ``validate.py`` check 1 needs the raw lines: a JSON that does not
    parse is itself a ledger-shape violation.  ``read_ledger`` cannot see
    it because it raises.
    """
    return [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def write_ledger_entry(path: Path, entry: dict[str, Any]) -> None:
    """Append one ledger entry (dict with the JSON key ``class``) as JSONL."""
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def _cc_names_src_path(cc: str) -> bool:
    """True when the closing condition names a ``<feature>/src/`` or
    ``<feature>/tests/`` path."""
    return "/src/" in cc or "/tests/" in cc


def _cc_has_test_command(cc: str) -> bool:
    """True when the closing condition names a test command."""
    lowered = cc.lower()
    return any(
        marker in lowered
        for marker in ("pytest ", "python3 -m pytest", "passes;", "gate:")
    )


def _cc_names_doc(cc: str) -> bool:
    """True when the closing condition names the source doc and the
    exact cell/value it sets (doc-edit verdicts).

    ``next_action_complete`` / ``next_action_pending`` name the source
    doc: "Set row <ID> Next Action to ... in <source_doc>".  ``doc_sync``
    names the source doc: "the doc edit lands in <source_doc>".
    ``fr_orphan`` names the feature's BACKLOG.md.
    """
    lowered = cc.lower()
    return "set row" in lowered or "set " in lowered or "backlog.md" in lowered


def verify_ledger_invariants(
    entries: Sequence[LedgerEntry | dict[str, Any]],
) -> list[InvariantViolation]:
    """Run checks 1-4 over a list of typed ledger entries.

    This is the shared engine behind ``validate.py`` checks 1-4:

    1. **Ledger shape** — ``class`` in the fixed vocabulary; ``action`` in
       the fixed vocabulary; ``closing_condition`` present and non-empty
       for every ``created`` / ``commented`` row and ``"—"`` for skip rows.
    2. **Closing-condition re-runnability (structural)** — for every
       ``created`` / ``commented`` row the ``closing_condition`` string
       must be re-runnable from the body alone.  Code-implementation
       verdicts name a ``<feature>/src/`` or ``<feature>/tests/`` path and
       a test command; doc-edit verdicts name the source doc and the
       exact cell/value.
    3. **Skip / Done evidence — split by ``action``**:
       (a) ``skipped-evidence`` rows require ``proof.evidence`` naming a
           source file and a test command;
       (b) ``skipped-exists`` rows require a populated ``issue`` number.
    4. **Incomplete → issue mapping** — every row with class in
       ``{incomplete, doc_sync, unverified, fr_orphan}`` must carry a
       non-empty ``issue`` number.
    """
    violations: list[InvariantViolation] = []
    for entry in entries:
        row_id = entry["row"] or "<unknown-row>"
        cls = entry["class_"]
        action = entry["action"]
        cc = entry["closing_condition"]

        # Check 1 — ledger shape.
        if cls not in CLASS_VOCABULARY:
            violations.append(
                InvariantViolation("class", f"class {cls!r} not in vocabulary", row_id)
            )
        if action not in ACTION_VOCABULARY:
            violations.append(
                InvariantViolation(
                    "action",
                    f"action {action!r} not in vocabulary",
                    row_id,
                )
            )
        if action in ("created", "commented") and not cc:
            violations.append(
                InvariantViolation(
                    "closing_condition",
                    f"action {action!r} requires a non-empty closing_condition",
                    row_id,
                )
            )
        if action in ("skipped-exists", "skipped-evidence") and cls in (
            "skip",
            "skip_next_action",
        ) and cc not in ("", "—"):
            violations.append(
                InvariantViolation(
                    "closing_condition",
                    f"skip row records closing_condition {cc!r}, expected \"—\" or empty",
                    row_id,
                )
            )

        # Check 2 — closing-condition re-runnability (created / commented).
        if action in ("created", "commented") and cc:
            if cls in _CC_CODE_CLASSES:
                if not _cc_names_src_path(cc):
                    violations.append(
                        InvariantViolation(
                            "closing_condition",
                            "code-implementation closing condition must name a "
                            "<feature>/src/ or <feature>/tests/ path",
                            row_id,
                        )
                    )
                if not _cc_has_test_command(cc):
                    violations.append(
                        InvariantViolation(
                            "closing_condition",
                            "code-implementation closing condition must name a "
                            "test command",
                            row_id,
                        )
                    )
            elif cls in _CC_DOC_EDIT_CLASSES:
                if not _cc_names_doc(cc):
                    violations.append(
                        InvariantViolation(
                            "closing_condition",
                            "doc-edit closing condition must name the source doc "
                            "path and the exact cell/value it sets",
                            row_id,
                        )
                    )

        # Check 3 — skip / Done evidence, split by action.
        # (a) skipped-evidence (class skip, no-trust path that exercised a
        #     code check): requires proof.evidence naming a source file and
        #     a test command.  Only meaningful when class == "skip"; a
        #     skip_next_action row carries no evidence obligation.
        if action == "skipped-evidence" and cls == "skip":
            evidence = entry["proof"]["evidence"]
            if not evidence:
                violations.append(
                    InvariantViolation(
                        "proof.evidence",
                        "skipped-evidence row has empty proof.evidence "
                        "(silently-dropped skip)",
                        row_id,
                    )
                )
            else:
                if not _cc_names_src_path(evidence):
                    violations.append(
                        InvariantViolation(
                            "proof.evidence",
                            "skipped-evidence proof must name a <feature>/src/ or "
                            "<feature>/tests/ file",
                            row_id,
                        )
                    )
                if not _cc_has_test_command(evidence):
                    violations.append(
                        InvariantViolation(
                            "proof.evidence",
                            "skipped-evidence proof must name a test command",
                            row_id,
                        )
                    )
        elif action == "skipped-exists":
            if not entry["issue"]:
                violations.append(
                    InvariantViolation(
                        "issue",
                        "skipped-exists row requires a populated issue number",
                        row_id,
                    )
                )

        # Check 4 — incomplete / doc_sync / unverified / fr_orphan → issue.
        if cls in _ISSUE_REQUIRED_CLASSES and not entry["issue"]:
            violations.append(
                InvariantViolation(
                    "issue",
                    f"class {cls!r} requires a non-empty issue number",
                    row_id,
                )
            )

    return violations
