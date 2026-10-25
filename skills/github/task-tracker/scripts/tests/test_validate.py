"""Unit tests for validate.py checks 1-6 and ledger.py invariants.

Uses the repo-local import shim so pytest (run from the repo root) can
import ``scripts.validate``; see ``scripts/tests/test_classify.py`` for
the same pattern. No network is used: the ``--gh`` path is gh-free in
the engine (``verify_ledger_invariants``) and is only exercised at the
flag level here.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

# Add the task-tracker skill root to sys.path so ``scripts.*`` is importable
# when pytest collects these tests from the repo root.
_SKILL_DIR = Path(__file__).resolve().parent.parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from scripts import ledger, validate
from scripts.ledger import LedgerEntry

LEDGER = Path(__file__).resolve().parent / "fixtures" / "sample_ledger.jsonl"


def _entries() -> list[LedgerEntry]:
    return ledger.read_ledger(LEDGER)
def test_read_ledger_parses_all_rows() -> None:
    entries = _entries()
    assert len(entries) == 6
    assert entries[0]["row"] == "WID-01"
    assert entries[0]["class_"] == "incomplete"
    assert entries[0]["action"] == "created"
    assert entries[0]["issue"] == 101
    assert entries[3]["row"] == "WID-04"
    assert entries[3]["action"] == "skipped-exists"
    assert entries[3]["issue"] == 102


def test_checks_1_to_4_clean_on_valid_ledger() -> None:
    entries = _entries()
    violations = ledger.verify_ledger_invariants(entries)
    assert violations == []


def test_check_1_malformed_line_is_a_violation(tmp_path: Path) -> None:
    bad = tmp_path / "bad.jsonl"
    bad.write_text(
        '{"run": "2026-10-25", "row": "X", "doc": "x", "feature": "root", '
        '"fr": [], "state": "Ready", "priority": "P0", "class": "incomplete", '
        '"proof": {"verdict": "open", "evidence": ""}, '
        '"closing_condition": "x/src/a.py implements b, exercised by x/tests/t.py; python3 -m pytest x/tests -q passes", '
        '"issue": 1, "action": "created"}\n'
        + "{not json}\n",
        encoding="utf-8",
    )
    lines = ledger.read_ledger_lines(bad)
    assert len(lines) == 2
    result = validate.run_checks(bad, None, gh_enabled=False)
    shape_violations = [v for v in result["violations"] if v["field"] == "ledger"]
    assert len(shape_violations) == 1
    assert "line 2" in shape_violations[0]["message"]
    assert result["exit_code"] == 1


def test_check_4_issue_required_for_actionable_class() -> None:
    entries = _entries()
    sc_violation: dict[str, Any] = dict(entries[0])
    sc_violation["issue"] = 0
    violations = ledger.verify_ledger_invariants([sc_violation])
    assert len(violations) == 1
    assert violations[0].field == "issue"
    assert violations[0].row_id == "WID-01"


def test_check_2_code_implementation_closing_condition_needs_path_and_command() -> None:
    entries = _entries()
    entry: dict[str, Any] = dict(entries[0])
    entry["closing_condition"] = "no path here"
    violations = ledger.verify_ledger_invariants([entry])
    assert any("src/" in v.message or "tests/" in v.message for v in violations)

    entry2: dict[str, Any] = dict(entries[0])
    entry2["closing_condition"] = "widgets/src/validator.py implements validate_widget"
    violations2 = ledger.verify_ledger_invariants([entry2])
    assert any("test command" in v.message for v in violations2)


def test_check_2_doc_edit_closing_condition_names_source_doc() -> None:
    entries = _entries()
    entry: dict[str, Any] = dict(entries[4])
    entry["class_"] = "doc_sync"
    entry["closing_condition"] = "just prose, no doc path"
    violations = ledger.verify_ledger_invariants([entry])
    assert any("source doc" in v.message for v in violations)

    entry2: dict[str, Any] = dict(entries[4])
    entry2["class_"] = "next_action_complete"
    entry2["closing_condition"] = (
        'Set row WEXT-01 Next Action to "none" in widgets-ext/BACKLOG.md '
        "(action already verified in code + tests)."
    )
    violations2 = ledger.verify_ledger_invariants([entry2])
    assert not any("source doc" in v.message for v in violations2)


def test_check_3_skipped_evidence_requires_path_and_command() -> None:
    entries = _entries()
    entry: dict[str, Any] = dict(entries[2])  # WID-03 skip + evidence
    violations = ledger.verify_ledger_invariants([entry])
    assert violations == []

    entry2: dict[str, Any] = dict(entries[2])
    entry2["proof"] = dict(entries[2]["proof"])
    entry2["proof"]["evidence"] = ""
    violations2 = ledger.verify_ledger_invariants([entry2])
    assert any("empty proof.evidence" in v.message for v in violations2)


def test_check_3_skipped_exists_requires_issue() -> None:
    entries = _entries()
    entry: dict[str, Any] = dict(entries[3])  # WID-04 skipped-exists + issue 102
    violations = ledger.verify_ledger_invariants([entry])
    assert violations == []

    entry2: dict[str, Any] = dict(entries[3])
    entry2["issue"] = 0
    violations2 = ledger.verify_ledger_invariants([entry2])
    assert any(
        "skipped-exists row requires a populated issue number" in v.message
        for v in violations2
    )
def test_check_5_deferred_without_report() -> None:
    result = validate.run_checks(LEDGER, None, gh_enabled=False)
    assert result["checks"]["invariant_count"] == "deferred-to-report"
    assert result["checks"]["run_report"] == "deferred-to-report"
    assert result["checks"]["gh_liveness"] == "deferred-to-gh"


def test_check_5_ok_with_report() -> None:
    report = {
        "rows_scanned": 6,
        "actionable_verdict_count": 3,
        "pending_infra": [],
        "invariant_ok": True,
    }
    with tempfile.TemporaryDirectory() as td:
        rpath = Path(td) / "report.json"
        rpath.write_text(json.dumps(report), encoding="utf-8")
        result = validate.run_checks(LEDGER, rpath, gh_enabled=False)
    assert result["checks"]["invariant_count"] == "ok"
    assert result["checks"]["run_report"] == "ok"


def test_check_5_violated_when_pending_infra_nonempty() -> None:
    report = {
        "rows_scanned": 6,
        "actionable_verdict_count": 3,
        "pending_infra": ["WID-01"],
        "invariant_ok": False,
    }
    with tempfile.TemporaryDirectory() as td:
        rpath = Path(td) / "report.json"
        rpath.write_text(json.dumps(report), encoding="utf-8")
        result = validate.run_checks(LEDGER, rpath, gh_enabled=False)
    assert result["checks"]["invariant_count"] == "violated"
    assert result["exit_code"] == 1


def test_check_6_half_written_report_tolerated() -> None:
    report = {"rows_scanned": 6, "actionable_verdict_count": 3}
    with tempfile.TemporaryDirectory() as td:
        rpath = Path(td) / "report.json"
        rpath.write_text(json.dumps(report), encoding="utf-8")
        result = validate.run_checks(LEDGER, rpath, gh_enabled=False)
    assert result["checks"]["run_report"] == "ok"
    # pending_infra absent → check 5 is deferred, not violated.
    assert result["checks"]["invariant_count"] == "deferred-to-report"


def test_main_writes_report_to_out(tmp_path: Path) -> None:
    out = tmp_path / "validate-report.json"
    report = {
        "rows_scanned": 6,
        "actionable_verdict_count": 3,
        "pending_infra": [],
        "invariant_ok": True,
    }
    rpath = tmp_path / "report.json"
    rpath.write_text(json.dumps(report), encoding="utf-8")
    code = validate.main(
        [
            "--repo-root",
            str(Path(__file__).resolve().parent.parent.parent),
            "--ledger",
            str(LEDGER),
            "--report",
            str(rpath),
            "--out",
            str(out),
        ]
    )
    assert code == 0
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["checks"]["invariant_count"] == "ok"
    assert written["violations_count"] == 0
