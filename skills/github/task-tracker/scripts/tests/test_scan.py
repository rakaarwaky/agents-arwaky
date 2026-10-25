from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "sample_repo"
DISCOVERY = REPO_ROOT / "discovery.json"

# Add the task-tracker skill root to sys.path so `scripts.*` is importable
# when pytest collects these tests from the repo root.
_SKILL_DIR = Path(__file__).resolve().parent.parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from scripts import scan


def _run() -> dict[str, Any]:
    return scan.run_scan(str(REPO_ROOT), str(DISCOVERY))


def test_output_doc_paths_include_in_scope_zero_rows_doc() -> None:
    result = _run()
    docs = [d["doc"] for d in result["docs"]]
    # Well-formed feature doc.
    assert "widgets/BACKLOG.md" in docs
    # In-scope zero-rows doc is present with rows: [] and a warning.
    assert "widgets-tools/BACKLOG.md" in docs
    by_doc = {d["doc"]: d for d in result["docs"]}
    zero_doc = by_doc["widgets-tools/BACKLOG.md"]
    assert zero_doc["rows"] == []
    assert zero_doc["warning"] is not None
    assert "zero rows" in zero_doc["warning"]
    # Multi-line-cell doc is present and parsed.
    assert "widgets-ext/BACKLOG.md" in docs


def test_scan_rows_extracted() -> None:
    result = _run()
    rows = result["rows"]
    by_id = {r["id"]: r for r in rows}
    assert by_id["WID-01"]["state"] == "In Progress"
    assert by_id["WID-01"]["fr_refs"] == ["FR-WID-001"]
    assert by_id["WID-02"]["next_action"] == "none"
    assert by_id["WID-03"]["state"] == "Done"
    # Multi-line-cell doc: the long cell values parse as single cells.
    assert by_id["WEXT-01"]["state"] == "In Progress"
    assert "hot-reload" in by_id["WEXT-01"]["title"]
    assert by_id["WEXT-01"]["source_doc"] == "widgets-ext/BACKLOG.md"
    # Root docs carry no task tables in this fixture → only feature rows.
    assert len(rows) == 5  # 4 widgets rows + 1 widgets-ext row
    # Roll-up tables (Feature + State, no ID) are NOT task rows.
    assert "widgets" not in by_id


def test_fr_sets_extracted() -> None:
    result = _run()
    fr = result["fr"]
    assert "FR-WID-005" in fr["fr_declared"]
    assert "FR-WID-001" in fr["fr_referenced"]
    assert "FR-WID-005" not in fr["fr_referenced"]  # declared-not-referenced


def test_rollup_row_extracted() -> None:
    result = _run()
    assert "widgets" in result["rollup_row"]
    assert "In Progress" in result["rollup_row"]


def test_doc_state_line_captured_for_backlog_owned_feature() -> None:
    # widgets/BACKLOG.md has `State: In Progress`; check parse_doc surfaces it.
    text = (REPO_ROOT / "widgets" / "BACKLOG.md").read_text(encoding="utf-8")
    _rows, declared, _refs, rollup, doc_state = scan.parse_doc(
        "widgets/BACKLOG.md", text, "widgets", "widgets"
    )
    assert doc_state == "In Progress"
    assert "FR-WID-005" in declared
    assert rollup is not None and "widgets" in rollup
