"""Classify ScanOutput rows with the deterministic pre-verifier classes.

Stdlib only. Takes scan.py's output JSON and applies the doc-determinable
portion of the task-tracker SKILL.md classification table. Pure over JSON:
no gh, no network, no reads of the feature source trees.

Deterministic classes (from the SKILL.md classification table):

- ``incomplete``          — state in {Ready, In Progress, In Review}
- ``skip_next_action``    — Next Action cell is empty, or exactly one word
                            that is ``none`` / ``<skip>`` (case-insensitive)
- ``skip``                — Done under --trust-mode trust
- ``proof_demand``        — Done under --trust-mode no-trust
- ``fr_orphan``           — FR-id set difference, both directions
- ``rollup_mismatch``     — roll-up claimed state != effective state
- ``next_action_pending`` / ``next_action_complete`` — generated when a
  pending Next Action cell is present; closing conditions come from
  templates.py (test_file / test_command substituted from the cell text
  when parseable, otherwise the raw action text).

All other verdicts leave ``closing_condition`` null: that is the LLM
verifier's job (fr_orphan, rollup_mismatch, doc_sync, unverified, open).
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any

# Import templates from the sibling module. When run as a standalone
# script (``python3 scripts/classify.py``) the scripts directory is on
# sys.path, so the top-level ``templates`` import works; when imported as
# the ``scripts.templates`` package module the ``scripts.templates``
# import works.
try:
    from scripts.templates import (
        closing_condition_next_action_pending,
        closing_condition_skip_next_action,
    )
except ModuleNotFoundError:
    from templates import (  # type: ignore[import-not-found,no-redef]
        closing_condition_next_action_pending,
        closing_condition_skip_next_action,
    )

# Worst-state ranking for per-feature effective state: In Progress > In
# Review > Ready > Done.
_STATE_RANK = {
    "in progress": 0,
    "in review": 1,
    "ready": 2,
    "done": 3,
}
_RANK_ORDER = ["In Progress", "In Review", "Ready", "Done"]

# Staleness: rows updated more than this many days ago get a flag.
STALENESS_DAYS = 14

_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_TEST_CMD_RE = re.compile(r"(?:Gate:\s*)?(python3 [^\n;`]+|pytest [^\n;`]+|lint-arwaky-cli [^\n;`]+)")
# A backtick-quoted test file path: `.../tests/...`
_TEST_PATH_RE = re.compile(r"`?((?:[\w./-]*/tests/[\w./-]+))`?")
# The doc-advance clause embedded in some Next Action cells:
# `then set row <ID> Next Action to "done" in <doc>`.
_ADVANCE_CLAUSE_RE = re.compile(r";\s*then set row [\w.-]+ Next Action to \"done\" in .*$")


def log(msg: str) -> None:
    print(f"[task-tracker:classify] {msg}", file=sys.stderr)


def _state_rank(state: str) -> int:
    return _STATE_RANK.get(state.strip().lower(), 99)


def _effective_state(states: list[str]) -> str:
    """Worst state present, ranked In Progress > In Review > Ready > Done."""
    ranks = [_state_rank(s) for s in states]
    if not ranks:
        return "Done"
    best = min(ranks)
    if best == 99:
        # Unknown state name: treat as incomplete, not Done.
        return "In Progress"
    return _RANK_ORDER[best]


def _na_word_count(cell: str) -> int:
    return len(cell.split())


def _is_skip_next_action(cell: str) -> bool:
    """Engine Fix 1 rule.

    Skip only when the trimmed cell is empty, or exactly one word and that
    word is ``none`` / ``<skip>`` (case-insensitive). Multi-word cells that
    merely contain ``none`` are NOT skipped.
    """
    trimmed = cell.strip()
    words = _na_word_count(trimmed)
    return words == 0 or (words == 1 and trimmed.lower() in ("none", "<skip>"))


def _row_state_category(state: str) -> str | None:
    """Deterministic row class from the state column, or None for Done."""
    s = state.strip().lower()
    if s in ("ready", "in progress", "in review"):
        return "incomplete"
    if s == "done":
        return None  # trust_mode decides skip vs proof_demand
    # Legacy/unknown states: the SKILL.md maps them to the simplified four;
    # deterministically we cannot, so hand to the verifier as a proof demand.
    return "incomplete"


def _parse_next_action_check(cell: str) -> dict[str, Any]:
    """Build the next_action_check payload for a pending Next Action cell.

    ``action_text`` is the trimmed cell minus the embedded doc-advance
    clause (the template re-appends it); ``test_command`` and ``test_file``
    are pulled from the cell when parseable, otherwise null.
    """
    trimmed = cell.strip()
    action_text = _ADVANCE_CLAUSE_RE.sub("", trimmed).strip().rstrip(";").strip()
    test_cmd_match = _TEST_CMD_RE.search(trimmed)
    test_file_match = _TEST_PATH_RE.search(trimmed)
    return {
        "action_text": action_text,
        "needs_verification": True,
        "test_command": test_cmd_match.group(1).strip() if test_cmd_match else None,
        "test_file": test_file_match.group(1) if test_file_match else None,
    }


def _staleness_flag(updated: str, today: tuple[int, int, int]) -> bool:
    """True when the row's Updated date is more than STALENESS_DAYS old."""
    if not updated:
        return False
    match = _DATE_RE.search(updated)
    if not match:
        return False
    y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
    delta_days = (datetime.date(today[0], today[1], today[2])
                  - datetime.date(y, m, d)).days
    return delta_days > STALENESS_DAYS


def classify_scan(
    scan: dict[str, Any],
    trust_mode: str = "no-trust",
    today: str | None = None,
) -> dict[str, Any]:
    """Apply the deterministic classification table to a ScanOutput dict.

    ``today`` (``YYYY-MM-DD``) overrides the staleness reference date in
    tests; production runs use the real date.

    The ScanOutput shape:

    - ``rows``: list of scan rows (``id``, ``feature``, ``state``,
      ``next_action``, ``source_doc``, ``updated``).
    - ``fr_groups``: ``{feature: {"fr_declared": [...], "fr_referenced": [...]}}``
      when the scan was grouped per feature; otherwise falls back to the
      top-level ``fr`` sets (used for a single-feature scan).
    - ``rollups``: ``[{"feature", "claimed_state"}]`` per feature roll-up
      row.

    ``next_action_complete`` is produced when a pending Next Action cell is
    already implemented in code + tests — doc-determinable only when the
    scan carries the implementation flag; the LLM verifier owns the
    actual code check. When the scan JSON carries no such flag, the
    pending action is emitted as ``next_action_pending`` (a doc-determinable
    proof demand) and the verifier confirms which of the two it is.
    """
    if today:
        parts = today.split("-")
        today_tuple = (int(parts[0]), int(parts[1]), int(parts[2])) if len(parts) == 3 else (1970, 1, 1)
    else:
        tz = datetime.UTC
        now = datetime.datetime.now(tz).date()
        today_tuple = (now.year, now.month, now.day)

    rows_in = scan.get("rows", [])
    fr_in = scan.get("fr", {})

    rows_in_with_feature = rows_in

    # FR groups: prefer per-feature groups; fall back to the flat fr sets.
    fr_groups: dict[str, dict[str, Any]] = scan.get("fr_groups", {})
    if not fr_groups and (fr_in.get("fr_declared") or fr_in.get("fr_referenced")):
        fr_groups["root"] = {
            "fr_declared": fr_in.get("fr_declared", []),
            "fr_referenced": fr_in.get("fr_referenced", []),
        }

    # Group rows by feature for effective-state computation.
    feature_rows: dict[str, list[dict[str, Any]]] = {}
    for row in rows_in_with_feature:
        feature_rows.setdefault(row.get("feature", "root"), []).append(row)

    feature_effective: dict[str, str] = {}
    for feature, frows in feature_rows.items():
        states = [r.get("state", "unknown") for r in frows]
        feature_effective[feature] = _effective_state(states)

    classified_rows: list[dict[str, Any]] = []
    staleness_flags: list[dict[str, Any]] = []

    for row in rows_in_with_feature:
        row_id = row.get("id", "")
        feature = row.get("feature", "root")
        state = row.get("state", "unknown")
        next_action = row.get("next_action", "")
        source_doc = row.get("source_doc", "")
        updated = row.get("updated", "")

        stale = _staleness_flag(updated, today_tuple)
        if stale:
            staleness_flags.append({"row_id": row_id, "feature": feature, "updated": updated})

        next_action_check: dict[str, Any] | None = None
        classification: str
        closing_condition: str | None = None

        if _is_skip_next_action(next_action):
            classification = "skip_next_action"
            closing_condition = closing_condition_skip_next_action()
        elif trust_mode == "trust" and state.strip().lower() == "done":
            classification = "skip"
        elif trust_mode != "trust" and state.strip().lower() == "done":
            # no-trust: a Done row is a proof demand for the verifier.
            classification = "proof_demand"
        else:
            # Ready / In Progress / In Review / legacy / unknown states.
            state_class = _row_state_category(state)
            if next_action.strip() and not _is_skip_next_action(next_action):
                next_action_check = _parse_next_action_check(next_action)
                test_cmd = next_action_check.get("test_command") or "the row's test command"
                test_file = next_action_check.get("test_file") or "the feature's test file"
                classification = "next_action_pending"
                closing_condition = closing_condition_next_action_pending(
                    feature=feature,
                    row_id=row_id,
                    action_description=next_action_check.get("action_text") or next_action,
                    test_file=test_file,
                    test_command=test_cmd,
                    source_doc=source_doc,
                )
            elif state_class is not None:
                classification = state_class
            else:
                classification = "incomplete"

        effective = feature_effective.get(feature, "Done")
        classified_rows.append(
            {
                "row_id": row_id,
                "feature": feature,
                "classification": classification,
                "next_action_check": next_action_check,
                "effective_state": effective,
                "staleness_flag": stale,
                "closing_condition": closing_condition,
            }
        )

    # FR orphans: set difference in both directions, per feature group.
    fr_orphans: list[dict[str, Any]] = []
    for feature, group in fr_groups.items():
        declared = set(group.get("fr_declared", []))
        referenced = set(group.get("fr_referenced", []))
        target_doc = f"{feature}/BACKLOG.md"
        for fr_id in sorted(declared - referenced):
            fr_orphans.append(
                {
                    "fr_id": fr_id,
                    "feature": feature,
                    "direction": "declared-not-referenced",
                    "target_doc": target_doc,
                    "closing_condition": None,
                }
            )
        for fr_id in sorted(referenced - declared):
            fr_orphans.append(
                {
                    "fr_id": fr_id,
                    "feature": feature,
                    "direction": "referenced-not-declared",
                    "target_doc": target_doc,
                    "closing_condition": None,
                }
            )

    # Roll-up mismatch: claimed state vs effective state per feature.
    rollup_mismatches: list[dict[str, Any]] = []
    for rollup in scan.get("rollups", []):
        feature = rollup.get("feature", "root")
        claimed = rollup.get("claimed_state", "")
        effective = feature_effective.get(feature, "Done")
        if claimed.strip().lower() != effective.strip().lower():
            rollup_mismatches.append(
                {
                    "feature": feature,
                    "claimed": claimed,
                    "effective": effective,
                    "verdict": "rollup_mismatch",
                    "closing_condition": None,
                }
            )

    counts = _verdict_counts(classified_rows, fr_orphans, rollup_mismatches)
    output = {
        "rows": classified_rows,
        "fr_orphans": fr_orphans,
        "rollup_mismatches": rollup_mismatches,
        "staleness_flags": staleness_flags,
        "trust_mode": trust_mode,
    }
    log(
        f"{len(classified_rows)} verdicts: "
        f"{counts['open']} open, {counts['doc_sync']} doc_sync, "
        f"{counts['unverified']} unverified, {counts['fr_orphan']} fr_orphan, "
        f"{counts['skip']} skip, {counts['pending_infra']} pending-infra"
    )
    return output


def _verdict_counts(
    rows: list[dict[str, Any]], fr_orphans: list[dict[str, Any]], rollups: list[dict[str, Any]]
) -> dict[str, int]:
    """Deterministic pre-verifier counts; verifier-owned buckets are 0 here.

    ``open`` counts incomplete rows; ``skip`` counts trust-mode skips plus
    skip_next_action; ``pending_infra`` counts no-trust proof demands that
    await the verifier (they are never counted as skips).
    """
    counts = {"open": 0, "doc_sync": 0, "unverified": 0, "fr_orphan": 0, "skip": 0, "pending_infra": 0}
    counts["fr_orphan"] = len(fr_orphans)
    counts["doc_sync"] = len(rollups)
    for row in rows:
        cls = row["classification"]
        if cls in ("incomplete", "next_action_pending", "next_action_complete"):
            counts["open"] += 1
        elif cls in ("skip", "skip_next_action"):
            counts["skip"] += 1
        elif cls == "proof_demand":
            counts["pending_infra"] += 1
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="classify.py")
    parser.add_argument("--repo-root", required=True, help="Absolute path to the AES repo.")
    parser.add_argument("--scan-out", required=True, help="scan.py output JSON.")
    parser.add_argument("--trust-mode", choices=["no-trust", "trust"], default="no-trust")
    parser.add_argument("--today", default=None, help="YYYY-MM-DD staleness reference date (tests).")
    parser.add_argument("--out", default=None, help="Write classified JSON here; default: stdout.")
    args = parser.parse_args(argv)

    scan = json.loads(Path(args.scan_out).read_text(encoding="utf-8"))
    classified = classify_scan(scan, trust_mode=args.trust_mode, today=args.today)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(classified, fh, indent=2)
            fh.write("\n")
    else:
        print(json.dumps(classified, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
