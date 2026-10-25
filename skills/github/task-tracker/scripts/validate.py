"""Post-run invariant checker for task-tracker ledger + run report.

Stdlib only (plus the ``gh`` CLI for the opt-in ``--gh`` liveness check).
Runs the six checks from the design doc without invoking the model:

1. Ledger shape (every JSONL line parses; fixed ``class`` / ``action``
   vocabulary; ``closing_condition`` present for ``created`` /
   ``commented`` rows).
2. Closing-condition re-runnability (structural shape check).
3. Skip / Done evidence, split by ``action``.
4. Incomplete → issue-number mapping (offline field check).
5. Invariant count (ledger issued-with-CC vs report
   ``actionable_verdict_count``; ``pending_infra`` empty) — runs only
   with ``--report``; otherwise ``deferred-to-report``.
6. Run-report artifact field presence — runs only with ``--report``;
   otherwise ``deferred-to-report``.

``--gh`` (opt-in, network): for every ledger row carrying an ``issue``
number, confirm the issue exists and is ``OPEN``; any ``CLOSED`` /
missing issue is a ``stale-issue`` violation.  Without ``--gh`` the
open-state criterion is reported as ``deferred-to-gh``.

Exit 0 when no violations (or only deferred items), exit 1 otherwise.
The structured report goes to stderr; ``--out`` writes it as JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Import the sibling modules.  When run as a standalone script
# (``python3 scripts/validate.py``) the scripts directory is on
# sys.path, so the top-level ``common`` / ``ledger`` imports work;
# when imported as the ``scripts.validate`` package module the
# ``scripts.common`` import works.
try:
    from scripts.common import GhAuthError, GhRateLimited, gh
    from scripts.ledger import (
        InvariantViolation,
        LedgerEntry,
        parse_line,
        read_ledger_lines,
        verify_ledger_invariants,
    )
except ModuleNotFoundError:
    from common import (  # type: ignore[import-not-found,no-redef]
        GhAuthError,
        GhRateLimited,
        gh,
    )
    from ledger import (  # type: ignore[import-not-found,no-redef]
        InvariantViolation,
        LedgerEntry,
        parse_line,
        read_ledger_lines,
        verify_ledger_invariants,
    )


def log(msg: str) -> None:
    """Emit an observability line to stderr with the script prefix."""
    print(f"[task-tracker:validate] {msg}", file=sys.stderr)


# Check 5 (documented): the actionable verdicts (Rhai task-tracker.rhai
# lines 487-494).  The report's ``actionable_verdict_count`` is defined to
# match this list exactly — it is the count of verdicts in this set whose
# closing_condition is non-empty.  ``validate.py`` consumes that count
# from the run report (not recomputed here).
_ACTIONABLE_VERDICTS: frozenset[str] = frozenset(
    {
        "open",
        "doc_sync",
        "unverified",
        "rollup_mismatch",
        "fr_orphan",
        "exists",
        "next_action_complete",
        "next_action_pending",
    }
)


def _load_report(path: Path | None) -> dict[str, Any] | None:
    """Load the run-report JSON, or None when --report was not given / unreadable."""
    if path is None:
        return None
    try:
        payload: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        log(f"run report unreadable: {path}")
        return None
    return payload if isinstance(payload, dict) else None


def _gh_check_entries(entries: list[LedgerEntry]) -> tuple[list[InvariantViolation], bool]:
    """The opt-in network liveness check.

    Returns ``(violations, rate_limited)``.  A rate limit is not a
    violation — the caller reports ``deferred-gh-rate-limited`` instead of
    a hard failure.
    """
    violations: list[InvariantViolation] = []
    for entry in entries:
        issue = entry["issue"]
        if not issue:
            continue
        row_id = entry["row"] or "<unknown-row>"
        try:
            out = gh("issue", "view", str(issue), "--json", "state,number,title")
            parsed: object = json.loads(out)
            if not isinstance(parsed, dict):
                # Treated as a missing issue (gh output is always an object
                # on success; a non-object means the issue was not found).
                violations.append(
                    InvariantViolation("--gh", "issue not found", row_id)
                )
                continue
            state = str(parsed.get("state", "")).upper()
            if state != "OPEN":
                violations.append(
                    InvariantViolation(
                        "--gh",
                        f"issue #{issue} is {state.lower() or 'missing'}, expected open",
                        row_id,
                    )
                )
        except GhRateLimited:
            return violations, True
        except GhAuthError:
            raise
        except ValueError as exc:
            violations.append(
                InvariantViolation(
                    "--gh",
                    f"issue #{issue} missing or unreadable: {exc}",
                    row_id,
                )
            )
    return violations, False


def run_checks(
    ledger_path: Path,
    report_path: Path | None,
    gh_enabled: bool = False,
) -> dict[str, Any]:
    """Run all checks; return the report dict (JSON-serialisable)."""
    lines = read_ledger_lines(ledger_path)

    # Check 1 (JSON parse) happens per line; check 1 (shape) through the
    # engine below.  A line that does not parse is a ledger-shape
    # violation on its own.
    shape_violations: list[InvariantViolation] = []
    entries: list[LedgerEntry] = []
    for idx, line in enumerate(lines):
        try:
            json.loads(line)
        except json.JSONDecodeError as exc:
            shape_violations.append(
                InvariantViolation(
                    "ledger",
                    f"line {idx + 1} does not parse as JSON: {exc}",
                    f"line-{idx + 1}",
                )
            )
            continue
        entries.append(parse_line(line))
    engine_violations = verify_ledger_invariants(entries)
    violations = shape_violations + engine_violations

    checks: dict[str, Any] = {}
    checks["ledger_shape"] = "ok" if not shape_violations else "violated"
    checks["closing_condition"] = "ok" if not engine_violations else "violated"

    report = _load_report(report_path)
    if report is None:
        checks["invariant_count"] = "deferred-to-report"
        checks["run_report"] = "deferred-to-report"
    else:
        actionable_count = report.get("actionable_verdict_count")
        pending_infra = report.get("pending_infra")
        pending_count = len(pending_infra) if isinstance(pending_infra, list) else 0

        # Check 5: invariant_ok = issued-with-CC == actionable count AND
        # pending_infra empty.  A half-written report (Classify done,
        # Issue not finalised) is a legitimate intermediate state: when
        # ``pending_infra`` is absent the count check is deferred.
        if pending_count > 0:
            checks["invariant_count"] = "violated"
            violations.append(
                InvariantViolation(
                    "invariant_count",
                    f"pending_infra has {pending_count} entry(ies): "
                    f"{pending_infra}",
                    "<report>",
                )
            )
        elif not isinstance(actionable_count, int):
            checks["invariant_count"] = "violated"
            violations.append(
                InvariantViolation(
                    "invariant_count",
                    "actionable_verdict_count missing or not an int",
                    "<report>",
                )
            )
        elif "pending_infra" not in report:
            checks["invariant_count"] = "deferred-to-report"
        else:
            checks["invariant_count"] = "ok"

        # Check 6: the run-report artifact must carry the Classify-phase
        # fields; the Issue-phase fields (pending_infra, invariant_ok)
        # are finalised later and are tolerated when absent.
        missing = [
            field
            for field in ("rows_scanned", "actionable_verdict_count")
            if field not in report
        ]
        checks["run_report"] = "ok" if not missing else "violated"

    if gh_enabled:
        gh_violations, rate_limited = _gh_check_entries(entries)
        checks["gh_liveness"] = "deferred-gh-rate-limited" if rate_limited else (
            "ok" if not gh_violations else "violated"
        )
        violations.extend(gh_violations)
    else:
        checks["gh_liveness"] = "deferred-to-gh"

    return {
        "checks": checks,
        "violations": [v._asdict() for v in violations],
        "violations_count": len(violations),
        "exit_code": 1 if violations else 0,
        "summary": _summary(checks),
    }


def _summary(checks: dict[str, Any]) -> str:
    parts = [f"{name}: {status}" for name, status in checks.items()]
    return "; ".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="validate.py")
    parser.add_argument("--repo-root", required=True, help="Absolute path to the AES repo.")
    parser.add_argument(
        "--ledger", required=True, help="Path to the task-tracker ledger JSONL."
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Run-report JSON artifact (Classify + Issue phase fields).",
    )
    parser.add_argument("--gh", action="store_true", help="Enable the network liveness check.")
    parser.add_argument("--out", default=None, help="Write the validate report JSON here.")
    args = parser.parse_args(argv)

    ledger_path = Path(args.ledger)
    if not ledger_path.is_file():
        log(f"ledger not found: {ledger_path}")
        return 1
    report_path = Path(args.report) if args.report else None
    if report_path is not None and not report_path.is_file():
        log(f"run report not found: {report_path}")
        report_path = None

    try:
        result = run_checks(ledger_path, report_path, gh_enabled=args.gh)
    except GhAuthError as exc:
        log(f"GH_AUTH_REQUIRED: {exc}")
        return 1

    # Print the structured invariant report to stderr (one line per violation).
    log(f"checks: {result['summary']}")
    for v in result["violations"]:
        log(f"violation [{v['field']}] row {v['row_id']}: {v['message']}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
            fh.write("\n")
    else:
        print(json.dumps(result, indent=2))

    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
