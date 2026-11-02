"""Tests for scripts/run.py (dry-run mode only; no network).

Uses the repo-local import shim so pytest (run from the repo root) can
import ``scripts.run``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_SKILL_DIR = Path(__file__).resolve().parent.parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from scripts import run

REPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "sample_repo"
DISCOVERY = REPO_ROOT / "discovery.json"


def _run_dry_run(tmp_path: Path) -> dict[str, Any]:
    report = tmp_path / "report.json"
    code = run.run(
        str(REPO_ROOT),
        str(DISCOVERY),
        str(tmp_path / "scan.json"),
        str(tmp_path / "classified.json"),
        "no-trust",
        True,
        str(tmp_path / "ledger.jsonl"),
        str(report),
    )
    return {"code": code, "report": report}


def test_run_dry_run_exits_zero_and_writes_report_only(tmp_path: Path) -> None:
    result = _run_dry_run(tmp_path)
    assert result["code"] == 0
    assert result["report"].is_file()
    report = json.loads(result["report"].read_text(encoding="utf-8"))
    assert report["rows_scanned"] == 5
    assert "closing_conditions" in report
    assert "pending_infra" in report
    assert "invariant_ok" in report
    # Dry-run does not write a ledger; ledger path may or may not exist.


def test_run_dry_run_report_phase_fields(tmp_path: Path) -> None:
    result = _run_dry_run(tmp_path)
    report = json.loads(result["report"].read_text(encoding="utf-8"))
    for field in ("rows_scanned", "incomplete", "doc_sync", "unverified",
                  "fr_orphan", "skipped", "created", "commented",
                  "rollup_mismatches", "closing_conditions",
                  "actionable_verdict_count", "pending_infra", "invariant_ok"):
        assert field in report, f"missing {field}"
    # Dry-run creates/comments nothing yet.
    assert report["created"] == 0
    assert report["commented"] == 0
