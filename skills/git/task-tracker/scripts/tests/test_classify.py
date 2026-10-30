from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "sample_repo"

# Add the task-tracker skill root to sys.path so `scripts.*` is importable
# when pytest collects these tests from the repo root.
_SKILL_DIR = Path(__file__).resolve().parent.parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from typing import Any

from scripts import classify, scan
from scripts.templates import (
    closing_condition_next_action_complete,
    closing_condition_skip_next_action,
)

# A fixed reference date so staleness assertions are deterministic.
TODAY = "2026-10-25"


def _scan() -> dict[str, Any]:
    discovery = REPO_ROOT / "discovery.json"
    return scan.run_scan(str(REPO_ROOT), str(discovery))


def test_next_action_pending_closing_condition_exact_string() -> None:
    sc = _scan()
    result = classify.classify_scan(sc, trust_mode="no-trust", today=TODAY)
    by_id = {r["row_id"]: r for r in result["rows"]}
    row = by_id["WID-01"]
    assert row["classification"] == "next_action_pending"
    # The action description is the imperative action only: the trailing
    # test-command clause ("`python3 … -q` passes") and the doc-advance
    # clause are both stripped, because the template re-appends the command
    # and the advance. Pinned as a literal, not recomputed through the
    # template, so drift in either the parser or the template is caught.
    assert row["closing_condition"] == (
        "widgets/src/ implements add `widgets/src/validator.py` exercising "
        "`validate_widget`, exercised by widgets/tests/the feature's test file; "
        "python3 -m pytest widgets/tests -q passes; then set row WID-01 "
        "Next Action to \"done\" in widgets/BACKLOG.md."
    )
    assert row["next_action_check"]["action_text"] == (
        "add `widgets/src/validator.py` exercising `validate_widget`"
    )
    assert row["next_action_check"]["test_command"] == "python3 -m pytest widgets/tests -q"
    assert row["next_action_check"]["test_file"] is None  # not backtick-quoted


def _classify_row(row: dict[str, Any]) -> dict[str, Any]:
    sc = {"rows": [row], "fr": {}, "rollup_row": ""}
    return classify.classify_scan(sc, trust_mode="no-trust", today=TODAY)["rows"][0]  # type: ignore[no-any-return]


def _classify_cell(cell: str) -> dict[str, Any]:
    sc = {"rows": [{"id": "W-1", "feature": "w", "state": "Ready",
                    "next_action": cell, "source_doc": "w/BACKLOG.md",
                    "updated": "2026-10-20"}], "fr": {}, "rollup_row": ""}
    return classify.classify_scan(sc, trust_mode="no-trust", today=TODAY)["rows"][0]  # type: ignore[no-any-return]


def test_next_action_pending_piped_test_command_stops_at_pipe() -> None:
    row = _classify_row({"id": "W-1", "feature": "w", "state": "Ready",
                        "next_action": ("add the gate; `python3 -m pytest w/tests -q | grep 3 passed` "
                                        "passes; then set row W-1 Next Action to \"done\" in w/BACKLOG.md."),
                        "source_doc": "w/BACKLOG.md", "updated": "2026-10-20"})
    # The test command is the command up to the first shell pipe; the
    # pipeline (`| grep …`) is not swallowed into the check string.
    assert row["next_action_check"]["test_command"] == "python3 -m pytest w/tests -q"
    assert row["closing_condition"] is not None
    assert "| grep" not in row["closing_condition"]
    assert row["closing_condition"] == (
        "w/src/ implements add the gate, exercised by w/tests/the feature's test file; "
        "python3 -m pytest w/tests -q passes; then set row W-1 Next Action to \"done\" in w/BACKLOG.md."
    )


def test_next_action_pending_requires_backticked_test_path() -> None:
    # Backtick-quoted path → substituted into the check. The template
    # re-prepends `{feature}/tests/` to the substituted test file, so a
    # backticked path that already carries the feature prefix renders
    # doubled (`w/tests/w/tests/test_x.py`) — that doubling is the
    # expected template behavior and is pinned here, not a bug.
    row = _classify_cell("add test in `w/tests/test_x.py`; `python3 -m pytest w/tests -q` passes; "
                         "then set row W-1 Next Action to \"done\" in w/BACKLOG.md.")
    assert row["next_action_check"]["test_file"] == "w/tests/test_x.py"
    assert "exercised by w/tests/w/tests/test_x.py" in row["closing_condition"]
    # Prose path without backticks → the generic placeholder, not the path.
    row2 = _classify_cell("add test in w/tests/test_x.py; `python3 -m pytest w/tests -q` passes; "
                          "then set row W-1 Next Action to \"done\" in w/BACKLOG.md.")
    assert row2["next_action_check"]["test_file"] is None
    assert "the feature's test file" in row2["closing_condition"]


def test_next_action_complete_closing_condition_exact_string() -> None:
    # Direct template-string assertion: the doc-determinable closing
    # condition for a next_action_complete verdict is a fixed one-liner.
    got = closing_condition_next_action_complete(
        row_id="WID-09", source_doc="widgets/BACKLOG.md"
    )
    assert got == (
        "Set row WID-09 Next Action to \"none\" in widgets/BACKLOG.md "
        "(action already verified in code + tests)."
    )


def test_skip_next_action_emits_dash() -> None:
    sc = _scan()
    result = classify.classify_scan(sc, trust_mode="no-trust", today=TODAY)
    by_id = {r["row_id"]: r for r in result["rows"]}
    assert by_id["WID-02"]["classification"] == "skip_next_action"
    assert by_id["WID-02"]["closing_condition"] == closing_condition_skip_next_action()
    assert by_id["WID-02"]["closing_condition"] == "—"
    # Multi-word cell containing "none" is NOT skipped (Engine Fix 1):
    # WID-04's next_action is "none" (single word), but the skip rule must
    # also reject multi-word cells; assert the rule directly.
    assert classify._is_skip_next_action("none") is True
    assert classify._is_skip_next_action("<skip>") is True
    assert classify._is_skip_next_action("None") is True
    assert classify._is_skip_next_action("") is True
    assert classify._is_skip_next_action("None — every row is Done") is False


def test_done_row_no_trust_is_proof_demand() -> None:
    sc = _scan()
    result = classify.classify_scan(sc, trust_mode="no-trust", today=TODAY)
    by_id = {r["row_id"]: r for r in result["rows"]}
    # WID-03 is Done with Next Action "none" → skip_next_action fires first
    # (the skip rule takes precedence over the trust-mode Done path). The
    # proof-demand path is exercised by the direct rule below.
    assert by_id["WID-03"]["classification"] == "skip_next_action"
    # Direct rule: a Done row with a non-skip Next Action → proof_demand.
    done_row = {"id": "WID-03", "feature": "widgets", "state": "Done",
                "next_action": "reproduce `abc1234`", "source_doc": "widgets/BACKLOG.md",
                "updated": "2026-10-20"}
    sc2 = dict(sc)
    sc2["rows"] = [done_row]
    result2 = classify.classify_scan(sc2, trust_mode="no-trust", today=TODAY)
    assert result2["rows"][0]["classification"] == "proof_demand"
    assert result2["rows"][0]["closing_condition"] is None


def test_done_row_trust_is_skip() -> None:
    sc = _scan()
    # Same precedence: skip_next_action fires before the trust-mode Done
    # path. Direct rule: a Done row with a non-skip Next Action under
    # trust mode → skip.
    done_row = {"id": "WID-03", "feature": "widgets", "state": "Done",
                "next_action": "reproduce `abc1234`", "source_doc": "widgets/BACKLOG.md",
                "updated": "2026-10-20"}
    sc2 = dict(sc)
    sc2["rows"] = [done_row]
    result2 = classify.classify_scan(sc2, trust_mode="trust", today=TODAY)
    assert result2["rows"][0]["classification"] == "skip"


def test_incomplete_states() -> None:
    sc = _scan()
    result = classify.classify_scan(sc, trust_mode="no-trust", today=TODAY)
    by_id = {r["row_id"]: r for r in result["rows"]}
    # WID-04 is In Review with Next Action "none" → skip_next_action takes
    # precedence over the incomplete state.
    assert by_id["WID-04"]["classification"] == "skip_next_action"

    def _classify_one(row: dict[str, Any], trust: str = "no-trust") -> dict[str, Any]:
        sc_copy = dict(sc)
        sc_copy["rows"] = [row]
        return classify.classify_scan(sc_copy, trust_mode=trust, today=TODAY)["rows"][0]  # type: ignore[no-any-return]

    # Ready row with a pending Next Action → next_action_pending.
    assert _classify_one({"id": "WID-02", "feature": "widgets", "state": "Ready",
                         "next_action": "spec the pipeline", "source_doc": "widgets/BACKLOG.md",
                         "updated": "2026-10-20"})["classification"] == "next_action_pending"
    # Empty Next Action cell → the skip rule (empty cell is skipped) beats
    # the incomplete-state rule; only rows whose Next Action survives the
    # skip check reach next_action_pending.
    assert _classify_one({"id": "WID-02", "feature": "widgets", "state": "Ready",
                         "next_action": "", "source_doc": "widgets/BACKLOG.md",
                         "updated": "2026-10-20"})["classification"] == "skip_next_action"
    # In Review row with a pending Next Action → next_action_pending.
    assert _classify_one({"id": "WID-04", "feature": "widgets", "state": "In Review",
                         "next_action": "merge PR #42", "source_doc": "widgets/BACKLOG.md",
                         "updated": "2026-10-20"})["classification"] == "next_action_pending"
    # Effective state is the worst state in the feature's row group.
    sc_copy = dict(sc)
    sc_copy["rows"] = [
        {"id": "WID-01", "feature": "widgets", "state": "In Progress",
         "next_action": "x", "source_doc": "widgets/BACKLOG.md", "updated": "2026-10-20"},
        {"id": "WID-03", "feature": "widgets", "state": "Done",
         "next_action": "none", "source_doc": "widgets/BACKLOG.md", "updated": "2026-10-20"},
    ]
    result4 = classify.classify_scan(sc_copy, trust_mode="no-trust", today=TODAY)
    assert result4["rows"][0]["effective_state"] == "In Progress"
    assert result4["rows"][1]["effective_state"] == "In Progress"


def test_staleness_flag() -> None:
    sc = _scan()
    result = classify.classify_scan(sc, trust_mode="no-trust", today=TODAY)
    by_id = {r["row_id"]: r for r in result["rows"]}
    # WID-03 updated 2026-09-01, reference date 2026-10-25 → 54 days > 14.
    assert by_id["WID-03"]["staleness_flag"] is True
    assert by_id["WID-01"]["staleness_flag"] is False
    flagged = {f["row_id"] for f in result["staleness_flags"]}
    assert "WID-03" in flagged
    assert "WID-01" not in flagged


def test_staleness_boundary_14_days() -> None:
    # STALENESS_DAYS=14: exactly 14 days old is NOT stale; 15 days is.
    def _row(updated: str) -> dict[str, Any]:
        return {"id": "X-1", "feature": "f", "state": "Ready",
                "next_action": "", "source_doc": "f/BACKLOG.md", "updated": updated}

    sc14 = {"rows": [_row("2026-10-11")], "fr": {}, "rollup_row": ""}
    assert classify.classify_scan(sc14, trust_mode="no-trust", today=TODAY)["rows"][0]["staleness_flag"] is False
    sc15 = {"rows": [_row("2026-10-10")], "fr": {}, "rollup_row": ""}
    assert classify.classify_scan(sc15, trust_mode="no-trust", today=TODAY)["rows"][0]["staleness_flag"] is True


def test_today_is_validated() -> None:
    # A malformed --today is a clear error, not a silent (1970, 1, 1)
    # fallback or a deep ValueError.
    with pytest.raises(SystemExit) as exc_info:
        classify.classify_scan({"rows": []}, trust_mode="no-trust", today="garbage")
    assert "invalid --today" in str(exc_info.value)
    with pytest.raises(SystemExit) as exc_info2:
        classify.classify_scan({"rows": []}, trust_mode="no-trust", today="2026-02-30")
    assert "invalid --today" in str(exc_info2.value)
    # A valid date works.
    result = classify.classify_scan({"rows": [], "fr": {}, "rollup_row": ""},
                                    trust_mode="no-trust", today="2026-10-25")
    assert result["rows"] == []


def test_non_string_row_cells_coerce_to_empty() -> None:
    # A JSON null next_action must not crash the run; it coerces to the
    # skip path (empty cell) instead of an AttributeError traceback.
    sc = {"rows": [
        {"id": "W-1", "feature": "w", "state": "Ready",
         "next_action": None, "source_doc": "w/BACKLOG.md", "updated": None},
    ], "fr": {}, "rollup_row": ""}
    result = classify.classify_scan(sc, trust_mode="no-trust", today=TODAY)
    assert result["rows"][0]["classification"] == "skip_next_action"
    assert result["rows"][0]["staleness_flag"] is False


def test_fr_orphan_flags() -> None:
    sc = _scan()
    # scan.py emits per-feature fr_groups; the widgets feature owns
    # FR-WID-005 (declared, no citing row) → declared-not-referenced.
    result = classify.classify_scan(sc, trust_mode="no-trust", today=TODAY)
    orphans = result["fr_orphans"]
    by_fr = {o["fr_id"]: o for o in orphans}
    assert by_fr["FR-WID-005"]["feature"] == "widgets"
    assert by_fr["FR-WID-005"]["direction"] == "declared-not-referenced"
    assert by_fr["FR-WID-005"]["target_doc"] == "widgets/BACKLOG.md"
    assert by_fr["FR-WID-005"]["closing_condition"] is None
    # Referenced-not-declared direction: an FR cited by a row but declared
    # nowhere in the feature doc. (scan.py's declared set is whole-doc, so a
    # fixture row's own FRD Ref always counts as declared — this direction
    # is exercised on a hand-built scan.)
    sc2 = dict(sc)
    sc2["fr_groups"] = {
        "widgets-ext": {"fr_declared": ["FR-WEXT-001"], "fr_referenced": ["FR-WEXT-001", "FR-WEXT-002"]},
    }
    res2 = classify.classify_scan(sc2, trust_mode="no-trust", today=TODAY)
    ext_orphans = {o["fr_id"]: o for o in res2["fr_orphans"] if o["feature"] == "widgets-ext"}
    assert ext_orphans["FR-WEXT-002"]["direction"] == "referenced-not-declared"
    assert ext_orphans["FR-WEXT-002"]["target_doc"] == "widgets-ext/BACKLOG.md"
    assert ext_orphans["FR-WEXT-002"]["closing_condition"] is None
    # Cross-feature contamination is gone: a widgets-ext referenced FR that
    # is not declared in widgets must NOT be flagged against the widgets
    # group (fr_groups keeps the sets per feature).
    for orphan in orphans:
        if orphan["feature"] == "widgets":
            assert orphan["fr_id"].startswith("FR-WID-")
    # fr_groups is the sole FR input: a scan carrying only the flat `fr`
    # sets (no fr_groups key) yields no orphans.
    legacy = {"rows": [{"id": "W-1", "feature": "w", "state": "Ready",
                        "next_action": "none", "source_doc": "w/BACKLOG.md",
                        "updated": "2026-10-20"}],
              "fr": {"fr_declared": ["FR-X-001"], "fr_referenced": []}}
    res2 = classify.classify_scan(legacy, trust_mode="no-trust", today=TODAY)
    assert res2["fr_orphans"] == []


def test_rollup_mismatch_flags() -> None:
    # scan.py emits the `rollups` key on the default path, so the mismatch
    # detector runs without any opt-in key injection.
    sc = _scan()
    assert [r["feature"] for r in sc["rollups"]] == ["widgets"]
    result = classify.classify_scan(sc, trust_mode="no-trust", today=TODAY)
    # widgets claims In Progress, effective is In Progress → no mismatch.
    assert result["rollup_mismatches"] == []
    # Over-claim: roll-up claims Done while the backlog is still In
    # Progress → mismatch.
    sc2 = _scan()
    sc2["rollups"] = [{"feature": "widgets", "claimed_state": "Done"}]
    result2 = classify.classify_scan(sc2, trust_mode="no-trust", today=TODAY)
    assert len(result2["rollup_mismatches"]) == 1
    mismatch = result2["rollup_mismatches"][0]
    assert mismatch["feature"] == "widgets"
    assert mismatch["claimed"] == "Done"
    assert mismatch["effective"] == "In Progress"
    assert mismatch["verdict"] == "rollup_mismatch"
    assert mismatch["closing_condition"] is None
    # Symmetric under-claim: roll-up claims In Progress while every row is
    # Done → mismatch.
    sc3 = _scan()
    sc3["rows"] = [
        {"id": "WID-01", "feature": "widgets", "state": "Done",
         "next_action": "none", "source_doc": "widgets/BACKLOG.md",
         "updated": "2026-10-20"},
    ]
    sc3["rollups"] = [{"feature": "widgets", "claimed_state": "In Progress"}]
    result3 = classify.classify_scan(sc3, trust_mode="no-trust", today=TODAY)
    mismatches3 = result3["rollup_mismatches"]
    assert len(mismatches3) == 1
    assert mismatches3[0]["feature"] == "widgets"
    assert mismatches3[0]["claimed"] == "In Progress"
    assert mismatches3[0]["effective"] == "Done"
    assert mismatches3[0]["verdict"] == "rollup_mismatch"
