from __future__ import annotations

import json
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


def _run(features_filter: list[str] | None = None) -> dict[str, Any]:
    return scan.run_scan(str(REPO_ROOT), str(DISCOVERY), features_filter=features_filter)


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
    assert {r["id"] for r in rows} == {"WID-01", "WID-02", "WID-03", "WID-04", "WEXT-01"}
    # Roll-up tables (Feature + State, no ID) are NOT task rows.
    assert "widgets" not in by_id


def test_fr_sets_extracted() -> None:
    result = _run()
    fr = result["fr"]
    assert "FR-WID-005" in fr["fr_declared"]
    assert "FR-WID-001" in fr["fr_referenced"]
    assert "FR-WID-005" not in fr["fr_referenced"]  # declared-not-referenced


def test_features_filter_limits_docs_and_unknown_feature_warns() -> None:
    result = _run(features_filter=["widgets", "not-a-feature"])
    docs = [d["doc"] for d in result["docs"]]
    assert docs == ["widgets/BACKLOG.md"]
    assert [r["id"] for r in result["rows"]] == [
        r["id"] for r in _run()["rows"] if r["feature"] == "widgets"
    ]


def test_unreadable_doc_emits_empty_rows_and_warning(tmp_path: Path) -> None:
    discovery = tmp_path / "discovery.json"
    discovery.write_text(
        json.dumps(
            {
                "root": [],
                "features": [
                    {"name": "ghost", "dir": "ghost", "docs": ["ghost/BACKLOG.md"]},
                ],
            }
        ),
        encoding="utf-8",
    )
    result = scan.run_scan(str(REPO_ROOT), str(discovery))
    assert result["docs"] == [
        {"doc": "ghost/BACKLOG.md", "rows": [], "warning": "unreadable: ghost/BACKLOG.md"}
    ]
    assert result["rows"] == []
    assert "unreadable doc: ghost/BACKLOG.md" in result["warnings"]


def test_rollup_row_extracted() -> None:
    result = _run()
    rollup_states = {r["feature"]: r["claimed_state"] for r in result["rollups"]}
    assert rollup_states.get("widgets") == "In Progress"


def test_rollups_key_carries_per_feature_claimed_state() -> None:
    result = _run()
    by_feature = {r["feature"]: r["claimed_state"] for r in result["rollups"]}
    # widgets/BACKLOG.md carries its own Feature Roll-up table claiming
    # In Progress; widgets-tools claims Ready; widgets-ext claims In Progress.
    assert by_feature == {
        "widgets": "In Progress",
        "widgets-tools": "Ready",
        "widgets-ext": "In Progress",
    }


def test_fr_groups_keyed_per_feature() -> None:
    result = _run()
    groups = result["fr_groups"]
    assert set(groups) == {"root", "widgets", "widgets-tools", "widgets-ext"}
    assert "FR-WID-005" in groups["widgets"]["fr_declared"]
    assert "FR-WID-005" not in groups["widgets"]["fr_referenced"]
    assert groups["widgets-ext"]["fr_referenced"] == ["FR-WEXT-001"]
    assert groups["widgets-tools"]["fr_declared"] == []
    assert groups["root"]["fr_declared"] == []


def test_doc_state_line_captured_for_backlog_owned_feature() -> None:
    # widgets/BACKLOG.md has `State: In Progress`; check parse_doc surfaces it.
    text = (REPO_ROOT / "widgets" / "BACKLOG.md").read_text(encoding="utf-8")
    _rows, declared, _refs, rollups, doc_state, _warnings = scan.parse_doc(
        "widgets/BACKLOG.md", text, "widgets", "widgets"
    )
    assert doc_state == "In Progress"
    assert "FR-WID-005" in declared
    assert {"feature": "widgets", "claimed_state": "In Progress"} in rollups


# --- aes-docs dialect: `## Roadmap Status` / `## Backlog Status` entry tables ---

_AES_ROADMAP = """# ROADMAP — sample

## Roadmap Status

### PR-SMP-001: filesystem

| Aspect       | Detail                                    |
|--------------|-------------------------------------------|
| Priority     | P0                                        |
| State        | Done                                      |
| Backlog      | [BACKLOG.md](crates/filesystem/BACKLOG.md) |
"""


def test_roadmap_status_entry_becomes_rollup_claim() -> None:
    rows, _decl, refs, rollups, _state, warnings = scan.parse_doc(
        "ROADMAP.md", _AES_ROADMAP, "root", "."
    )
    assert rows == []
    assert refs == []
    assert rollups == [
        {"feature": "crates/filesystem", "claimed_state": "Done"}
    ]
    assert warnings == []


_AES_BACKLOG = """# BACKLOG — filesystem

## Backlog Status

### FR-FS-001: reads a file

| Aspect       | Detail                            |
|--------------|-----------------------------------|
| State        | In Progress                       |
| Done         | Not done yet                      |
| Updated      | 2026-10-26                        |
"""


def test_backlog_status_entry_becomes_task_row_without_next_action() -> None:
    rows, _decl, refs, rollups, _state, warnings = scan.parse_doc(
        "crates/filesystem/BACKLOG.md", _AES_BACKLOG, "crates/filesystem",
        "crates/filesystem",
    )
    assert rollups == []
    assert warnings == []
    assert len(rows) == 1
    row = rows[0]
    assert row["id"] == "FR-FS-001"
    assert row["title"] == "reads a file"
    assert row["state"] == "In Progress"
    assert row["updated"] == "2026-10-26"
    assert row["feature"] == "crates/filesystem"
    assert row["source_doc"] == "crates/filesystem/BACKLOG.md"
    # The Aspect/Detail shape has no Next Action column → no key at all,
    # so classify.py's Engine Fix 1 skip rule cannot fire on this row.
    assert "next_action" not in row
    # FR-family entries count as backlog references for the orphan check.
    assert row["fr_refs"] == ["FR-FS-001"]
    assert refs == ["FR-FS-001"]


def test_bare_id_entry_heading_without_colon_is_a_row() -> None:
    # lint-arwaky's real crate BACKLOGs write `### FR-Filesystem-001` with
    # no `: title` — the template shows a title, the files often omit it.
    text = """# BACKLOG — filesystem

## Backlog Status

### FR-Filesystem-001

| Aspect | Detail |
| -------------- | --------------------------------------------- |
| State | Ready |
| Updated | 2026-09-29 |

## Reference

| Artifact | Purpose |
| --- | --- |
| PRD.md | spec |
"""
    rows, decl, refs, rollups, _state, warnings = scan.parse_doc(
        "crates/filesystem/BACKLOG.md", text, "crates/filesystem",
        "crates/filesystem",
    )
    # Mixed-case scopes register as declared too (FR_ID_RE is case-faithful).
    assert "FR-Filesystem-001" in decl
    assert warnings == []
    assert rollups == []
    assert len(rows) == 1
    row = rows[0]
    assert row["id"] == "FR-Filesystem-001"
    assert row["title"] == ""
    assert row["state"] == "Ready"
    assert row["fr_refs"] == ["FR-Filesystem-001"]
    assert refs == ["FR-Filesystem-001"]
    assert "next_action" not in row
    # row_text carries the bare ID (no dangling colon + blank title).
    assert row["row_text"].startswith("FR-Filesystem-001 | ")


def test_entry_table_outside_status_section_is_ignored() -> None:
    # The same entry + Aspect/Detail shape under any other H2 (e.g. a PRD's
    # Project Requirements) is not a backlog row and not a roll-up claim.
    text = """# PRD

## Project Requirements

### PR-SMP-001: something

| Aspect | Detail |
|---|---|
| State | Done |
| Backlog | [BACKLOG.md](crates/x/BACKLOG.md) |
"""
    rows, _decl, _refs, rollups, _state, warnings = scan.parse_doc(
        "PRD.md", text, "root", "."
    )
    assert rows == []
    assert rollups == []
    assert warnings == []


def test_roadmap_status_entry_without_feature_link_warns() -> None:
    text = _AES_ROADMAP.replace(
        "[BACKLOG.md](crates/filesystem/BACKLOG.md)", "BACKLOG.md"
    )
    rows, _decl, _refs, rollups, _state, warnings = scan.parse_doc(
        "ROADMAP.md", text, "root", "."
    )
    assert rows == []
    assert rollups == []
    assert any("without a feature Backlog link" in w for w in warnings)


def test_entry_context_is_scoped_to_its_own_h2() -> None:
    # An entry heading under one H2 cannot authorize a table under the next:
    # a bare Aspect/Detail table under Backlog Status (no entry) yields
    # nothing, while the Roadmap Status entry above still yields its claim.
    text = _AES_ROADMAP + (
        "\n## Backlog Status\n\n| Aspect | Detail |\n|---|---|\n| State | Ready |\n"
    )
    rows, _decl, _refs, rollups, _state, warnings = scan.parse_doc(
        "ROADMAP.md", text, "root", "."
    )
    assert rollups == [{"feature": "crates/filesystem", "claimed_state": "Done"}]
    assert rows == []
    assert warnings == []
