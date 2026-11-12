"""Issue-maker driver: scan → classify → open issues → ledger + report → validate.

One run covers one repo. Direction: repo → issues only. Never edits source,
never creates a branch, never opens a PR.

Default run is LIVE: steps 1–6 execute and `gh issue create` is called for
every actionable row. `--dry-run` executes steps 1–2 and prints every
would-be title/body/label without calling gh, writing ledger, or running
validate.

Exit 0 when no violations; exit 1 otherwise.
"""

from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

# Import sibling modules with the same shim used by the other scripts.
try:
    from scripts import classify, scan
    from scripts.common import GhAuthError
    from scripts.ledger import write_ledger_entry
except ModuleNotFoundError:  # pragma: no cover - standalone script path
    import classify  # type: ignore[no-redef, import-not-found]
    import scan  # type: ignore[no-redef, import-not-found]
    from common import GhAuthError  # type: ignore[no-redef, import-not-found]
    from ledger import write_ledger_entry  # type: ignore[no-redef, import-not-found]


def log(msg: str) -> None:
    print(f"[task-tracker:run] {msg}", file=sys.stderr)


def _now_iso() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _gh_issue_create(title: str, body: str, labels: list[str]) -> int | None:
    """Create an issue via gh; return its number, or None on failure."""
    args = ["gh", "issue", "create", "--title", title, "--body", body]
    for label in labels:
        args += ["--label", label]
    proc = subprocess.run(args, capture_output=True, text=True)  # noqa: PLW1510
    if proc.returncode != 0:
        log(f"gh issue create failed: {proc.stderr.strip()}")
        return None
    out = proc.stdout.strip()
    if out.isdigit():
        return int(out)
    digits = "".join(ch for ch in out.split("/")[-1] if ch.isdigit())
    return int(digits) if digits else None


def _state_label(state: str) -> str:
    return {
        "ready": "state:ready",
        "in progress": "state:in-progress",
        "in review": "state:in-review",
        "done": "state:done",
    }.get(state.strip().lower(), "state:—")


def _labels_for(classification: str, state: str) -> list[str]:
    labels = ["task-tracker", _state_label(state)]
    if classification in ("fr_orphan", "rollup_mismatch", "doc_sync", "unverified"):
        labels.append("doc-sync")
    else:
        labels.append("p1")
    return labels


def _title_for(row: dict[str, Any], classification: str) -> str:
    row_id = row.get("row_id", "")
    feature = row.get("feature", "root")
    title_prefix = {
        "incomplete": f"[{feature}] {row_id} — ",
        "doc_sync": f"[DOC-SYNC] {row_id} — ",
        "unverified": f"[{feature}] {row_id} — ",
        "fr_orphan": f"[DOC-SYNC] {feature} FR {row_id} — ",
        "rollup_mismatch": f"[DOC-SYNC] {feature} roll-up — ",
        "next_action_pending": f"[{feature}] {row_id} — ",
        "next_action_complete": f"[{feature}] {row_id} — ",
    }.get(classification, f"[{feature}] {row_id} — ")
    row_text = row.get("row_text", "") or row.get("state", "")
    summary = row_text.split("|")[0].strip() if row_text else f"{feature}: {row.get('state','unknown')}"
    return f"{title_prefix}{summary[:80]}"


def _build_issue_body(row: dict[str, Any], classification: str) -> str:
    cc = row.get("closing_condition") or ""
    next_action_check = row.get("next_action_check") or {}
    feature = row.get("feature", "root")
    row_id = row.get("row_id", "")
    source_doc = row.get("source_doc", "")
    state = row.get("state", "unknown")
    priority = row.get("priority", "—")
    health = row.get("health", "—")
    fr_refs = row.get("fr_refs") or []
    if not fr_refs and row.get("fr"):
        fr_refs = row["fr"]

    lines: list[str] = []
    lines.append(f"Source: `{source_doc}` · row `{row_id}` · scanned by `/issue-maker` on `{_now_iso()[:10]}`")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| State (doc) | {state} |")
    lines.append(f"| Priority | {priority} |")
    lines.append(f"| Health | {health} |")
    lines.append("| Owner | — |")
    lines.append("| Target | — |")
    lines.append(f"| Classification | {classification} |")
    if fr_refs:
        lines.append(f"| FR | {', '.join(fr_refs)} |")
    lines.append("")
    lines.append("## Task")
    if classification == "next_action_pending":
        lines.append(next_action_check.get("action_text") or row.get("row_text", "") or "")
    else:
        lines.append(row.get("row_text", "") or state)
    lines.append("")
    lines.append("## Evidence in doc")
    lines.append(f"> {row.get('row_text', '') or state}")
    lines.append("")
    lines.append("## Verification")
    if classification == "next_action_pending":
        test_file = next_action_check.get("test_file") or "the feature's test file"
        test_command = next_action_check.get("test_command") or "the row's test command"
        lines.append(
            f"{feature}/src/ implements the row's behavior, exercised by "
            f"{test_file}; `{test_command}` passes."
        )
    elif classification == "fr_orphan":
        lines.append(
            f"Confirm `{row_id}` is declared in the feature's FRD and add a backlog row "
            f"that cites it, then set that row to Done."
        )
    elif classification == "rollup_mismatch":
        claimed = row.get("claimed_state") or state
        effective = row.get("effective_state") or "Done"
        lines.append(
            f"Reconcile `{feature}`'s roll-up claim ({claimed}) with its backlog "
            f"effective state ({effective}); correct the doc that disagrees with code."
        )
    else:
        lines.append("Re-prove the row's claim against live source and test evidence at HEAD.")
    lines.append("")
    lines.append("## Roll-up check")
    effective = row.get("effective_state") or "Done"
    lines.append(f"{feature}: roll-up claims {row.get('claimed_state') or state}; "
                 f"backlog effective state {effective}; offending rows: {row_id} ({state}).")
    lines.append("")
    lines.append("## Closing condition")
    lines.append("**Check:** " + (cc or "no closing condition recorded"))
    lines.append("")
    lines.append("**Advance:** when the check passes, set row "
                 f"`{row_id}` `State` to `Done` in `{source_doc}` and write the "
                 "commit SHA + command output into its evidence cell. Every FR ID "
                 "cited by the row carries to `Done` with it.")
    lines.append("")
    lines.append("**Proof:** close this issue with the commit link and the command "
                 "output. No proof, no close, no `Done`.")
    return "\n".join(lines)


def _run_validate(repo_root: str, ledger_path: str, report_path: str | None) -> dict[str, Any]:
    args = [sys.executable, str(Path(__file__).with_name("validate.py")),
            "--repo-root", repo_root,
            "--ledger", ledger_path]
    if report_path:
        args += ["--report", report_path]
    proc = subprocess.run(args, capture_output=True, text=True)  # noqa: PLW1510
    if proc.returncode != 0:
        log(proc.stderr.strip())
        raise RuntimeError("validate.py exited non-zero")
    try:
        return cast("dict[str, Any]", json.loads(proc.stdout.strip() or "{}"))
    except json.JSONDecodeError:
        return {}


def _enrich_rows(classified: dict[str, Any], scan_payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Merge scan row data into classified rows (classify.py drops most fields)."""
    scan_rows = {r.get("id"): r for r in scan_payload.get("rows", [])}
    enriched: list[dict[str, Any]] = []
    for r in classified.get("rows", []):
        merged = dict(scan_rows.get(r.get("row_id", r.get("id")), {}))
        merged.update(r)
        merged["row_id"] = r.get("row_id")
        enriched.append(merged)
    return enriched


def run(repo_root: str,
        discovery: str | None,
        scan_out: str | None,
        classify_out: str | None,
        trust_mode: str,
        dry_run: bool,
        ledger_path: str,
        report_path: str | None) -> int:
    started = _now_iso()
    repo = Path(repo_root).resolve()
    if not repo.is_dir():
        log(f"repo root not found: {repo}")
        return 1

    # Step 1 — scan.
    scan_payload: dict[str, Any]
    if scan_out and Path(scan_out).is_file():
        scan_payload = json.loads(Path(scan_out).read_text(encoding="utf-8"))
        log(f"read existing scan output: {scan_out}")
    else:
        disc = discovery or str(repo / "docs" / "feature_schema.json")
        if not Path(disc).is_file():
            log(f"discovery JSON not found: {disc}")
            return 1
        scan_payload = scan.run_scan(str(repo), disc, out=scan_out)

    # Step 2 — classify.
    classified: dict[str, Any]
    if classify_out and Path(classify_out).is_file():
        classified = json.loads(Path(classify_out).read_text(encoding="utf-8"))
        log(f"read existing classify output: {classify_out}")
    else:
        classified = classify.classify_scan(scan_payload, trust_mode=trust_mode)
        if classify_out:
            Path(classify_out).write_text(
                json.dumps(classified, indent=2) + "\n", encoding="utf-8")

    rows = _enrich_rows(classified, scan_payload)
    fr_orphans = classified.get("fr_orphans", [])
    rollup_mismatches = classified.get("rollup_mismatches", [])

    # Phase 1 report fields.
    actionable = {"open", "doc_sync", "unverified", "rollup_mismatch", "fr_orphan",
                  "next_action_complete", "next_action_pending"}
    incomplete = sum(1 for r in rows if r["classification"] == "incomplete")
    doc_sync = sum(1 for r in rows if r["classification"] == "doc_sync")
    unverified = sum(1 for r in rows if r["classification"] == "unverified")
    skipped = sum(1 for r in rows if r["classification"] in ("skip", "skip_next_action"))

    # Actionable rows with a closing condition.
    issued_rows: list[dict[str, Any]] = []
    pending_infra: list[str] = []

    for r in rows:
        cls = r["classification"]
        if cls not in actionable:
            continue
        cc = r.get("closing_condition") or ""
        if not cc:
            pending_infra.append(r["row_id"])
            continue
        issued_rows.append(r)

    for fo in fr_orphans:
        if fo.get("closing_condition"):
            issued_rows.append(fo)
        else:
            pending_infra.append(fo.get("fr_id", "<fr-orphan>"))

    for rm in rollup_mismatches:
        if rm.get("closing_condition"):
            issued_rows.append(rm)
        else:
            pending_infra.append(rm.get("feature", "<rollup>"))

    closing_conditions = len(issued_rows)
    actionable_verdict_count = closing_conditions

    report_phase1: dict[str, Any] = {
        "rows_scanned": len(rows),
        "incomplete": incomplete,
        "doc_sync": doc_sync,
        "unverified": unverified,
        "fr_orphan": len(fr_orphans),
        "skipped": skipped,
        "created": 0,
        "commented": 0,
        "rollup_mismatches": len(rollup_mismatches),
        "closing_conditions": closing_conditions,
        "actionable_verdict_count": actionable_verdict_count,
    }

    # DRY-RUN: print would-be issues, exit 0. No ledger, no validate, no gh.
    if dry_run:
        log(f"DRY-RUN: {closing_conditions} would-be issue(s); "
            f"{len(pending_infra)} pending-infra")
        for r in issued_rows:
            cls = r["classification"]
            title = _title_for(r, cls)
            body = _build_issue_body(r, cls)
            labels = _labels_for(cls, r.get("state", "unknown"))
            print("=" * 80)
            print(title)
            print("-" * 80)
            print(body)
            print("-" * 80)
            print(f"labels: {','.join(labels)}")
        print("=" * 80)
        if report_path:
            report = dict(report_phase1)
            report["pending_infra"] = pending_infra
            report["invariant_ok"] = (len(pending_infra) == 0)
            Path(report_path).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return 0

    # Step 3–5 — open issues (live) + ledger.
    ledger_entries: list[dict[str, Any]] = []
    run_id = started[:10]

    def emit_ledger(row: dict[str, Any], cls: str, issue: int | None,
                    action: str, evidence: str = "") -> None:
        fr = row.get("fr_refs") or []
        if not fr and row.get("fr"):
            fr = row["fr"]
        entry: dict[str, Any] = {
            "run": run_id,
            "row": row.get("row_id", row.get("fr_id", row.get("feature", ""))),
            "doc": row.get("source_doc", row.get("target_doc", "")),
            "feature": row.get("feature", "root"),
            "fr": fr,
            "state": row.get("state", "unknown"),
            "priority": row.get("priority", "—"),
            "class": cls,
            "proof": {"verdict": cls, "evidence": evidence},
            "closing_condition": row.get("closing_condition") or "—",
            "issue": int(issue or 0),
            "action": action,
        }
        if entry["action"] in ("created", "commented") and not entry["closing_condition"]:
            entry["closing_condition"] = "—"
        ledger_entries.append(entry)

    created_count = 0
    commented_count = 0

    for r in issued_rows:
        cls = r["classification"]
        title = _title_for(r, cls)
        body = _build_issue_body(r, cls)
        labels = _labels_for(cls, r.get("state", "unknown"))
        issue: int | None = _gh_issue_create(title, body, labels)
        action = "created" if issue else "commented"
        emit_ledger(r, cls, issue, action,
                    evidence=f"{cls}: {r.get('row_text','')[:120]}")
        if issue:
            created_count += 1
        else:
            commented_count += 1

    # Write ledger (append mode so re-runs accumulate).
    ledger_p = Path(ledger_path)
    if not ledger_p.parent.is_dir():
        ledger_p.parent.mkdir(parents=True, exist_ok=True)
    for entry in ledger_entries:
        write_ledger_entry(ledger_p, entry)

    # Phase 2 — finalize report.
    if report_path:
        report = dict(report_phase1)
        report["created"] = created_count
        report["commented"] = commented_count
        report["pending_infra"] = pending_infra
        report["invariant_ok"] = (len(pending_infra) == 0)
        report["actionable_verdict_count"] = created_count + commented_count
        Path(report_path).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    # Step 6 — validate.
    try:
        result = _run_validate(str(repo), ledger_path, report_path)
    except GhAuthError:
        log("GH_AUTH_REQUIRED: resolve auth with the github-workflow skill, or pass --dry-run")
        return 1

    violations = result.get("violations", [])
    if violations:
        for v in violations:
            log(f"violation [{v.get('field')}] row {v.get('row_id')}: {v.get('message')}")
        return 1

    log(f"run complete: {created_count} created, {commented_count} commented, "
        f"{len(pending_infra)} pending-infra, validate ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run.py")
    parser.add_argument("--repo-root", required=True, help="Absolute path to the AES repo.")
    parser.add_argument("--discovery", default=None, help="Discovery JSON (feature_schema).")
    parser.add_argument("--scan-out", default=None, help="Write/read ScanOutput JSON here.")
    parser.add_argument("--classify-out", default=None, help="Write/read classified JSON here.")
    parser.add_argument("--trust-mode", choices=["no-trust", "trust"], default="no-trust")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print would-be issues without calling gh issue create.")
    parser.add_argument("--ledger", default=None,
                        help="Ledger JSONL path (default <repo>/docs/task-tracker-ledger.jsonl).")
    parser.add_argument("--report", default=None,
                        help="Run-report JSON path (default <repo>/docs/task-tracker-report.json).")
    args = parser.parse_args(argv)

    ledger_path = args.ledger or str(Path(args.repo_root) / "docs" / "task-tracker-ledger.jsonl")
    report_path = args.report or str(Path(args.repo_root) / "docs" / "task-tracker-report.json")

    return run(args.repo_root, args.discovery, args.scan_out, args.classify_out,
               args.trust_mode, args.dry_run, ledger_path, report_path)


if __name__ == "__main__":
    raise SystemExit(main())
