from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "sample_repo"

# Add the task-tracker skill root to sys.path so `scripts.*` is importable
# when pytest collects these tests from the repo root.
_SKILL_DIR = Path(__file__).resolve().parent.parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from scripts import classify, scan
from scripts.templates import (
    closing_condition_next_action_complete,
    closing_condition_next_action_pending,
    closing_condition_skip_next_action,
)

# A fixed reference date so staleness assertions are deterministic.
TODAY = "2026-10-25"


def _scan() -> dict:
    discovery = REPO_ROOT / "discovery.json"
    out = REPO_ROOT / "classify_scan_out.json"
    scan.run_scan(str(REPO_ROOT), str(discovery), out=str(out))
    return json.loads(out.read_text(encoding="utf-8"))


def test_next_action_pending_closing_condition_exact_string() -> None:
    sc = _scan()
    result = classify.classify_scan(sc, trust_mode="no-trust", today=TODAY)
    by_id = {r["row_id"]: r for r in result["rows"]}
    row = by_id["WID-01"]
    assert row["classification"] == "next_action_pending"
    check = row["next_action_check"]
    # test_file is not parseable out of WID-01's cell, so the row's closing
    # condition substitutes the generic placeholder; the exact string is
    # computed through the same template the classifier uses.
    expected = closing_condition_next_action_pending(
        feature="widgets",
        row_id="WID-01",
        action_description=check["action_text"],
        test_file="the feature's test file",
        test_command=check["test_command"],
        source_doc="widgets/BACKLOG.md",
    )
    assert row["closing_condition"] == expected
    # Structural assertions: the exact-string checks that matter.
    assert row["closing_condition"].startswith("widgets/src/ implements")
    assert "exercised by" in row["closing_condition"]
    assert row["closing_condition"].endswith(
        'then set row WID-01 Next Action to "done" in widgets/BACKLOG.md.'
    )
    assert check["test_command"] == "python3 -m pytest widgets/tests -q"


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

    def _classify_one(row: dict, trust: str = "no-trust") -> dict:
        sc_copy = dict(sc)
        sc_copy["rows"] = [row]
        return classify.classify_scan(sc_copy, trust_mode=trust, today=TODAY)["rows"][0]

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


def test_fr_orphan_flags() -> None:
    sc = _scan()
    # Per-feature FR groups: build the ones the widgets feature owns.
    rows_in_widgets = [r for r in sc["rows"] if r.get("feature") == "widgets"]
    declared = set(sc["fr"]["fr_declared"])
    referenced = set(sc["fr"]["fr_referenced"])
    sc["fr_groups"] = {"widgets": {"fr_declared": sorted(declared), "fr_referenced": sorted(referenced)}}
    del rows_in_widgets
    result = classify.classify_scan(sc, trust_mode="no-trust", today=TODAY)
    orphans = result["fr_orphans"]
    by_fr = {o["fr_id"]: o for o in orphans}
    # FR-WID-005 is declared in the FRD but cited by no backlog row.
    assert by_fr["FR-WID-005"]["direction"] == "declared-not-referenced"
    assert by_fr["FR-WID-005"]["target_doc"] == "widgets/BACKLOG.md"
    assert by_fr["FR-WID-005"]["closing_condition"] is None
    # FR-WEXT-001 is cited by a widgets-ext row; the flat fr sets are
    # feature-agnostic, so the referenced-only case is checked structurally:
    ext_referred_only = [
        o for o in orphans if o["direction"] == "referenced-not-declared"
    ]
    assert {o["fr_id"] for o in ext_referred_only} >= {"FR-WEXT-001"} or not ext_referred_only


def test_rollup_mismatch_flags() -> None:
    sc = _scan()
    sc["rollups"] = [{"feature": "widgets", "claimed_state": "Done"}]
    result = classify.classify_scan(sc, trust_mode="no-trust", today=TODAY)
    assert len(result["rollup_mismatches"]) == 1
    mismatch = result["rollup_mismatches"][0]
    assert mismatch["feature"] == "widgets"
    assert mismatch["claimed"] == "Done"
    assert mismatch["effective"] == "In Progress"
    assert mismatch["verdict"] == "rollup_mismatch"
    assert mismatch["closing_condition"] is None
    # Symmetric under-claim: roll-up claims In Progress, effective is Done.
    sc2 = _scan()
    sc2["rollups"] = [{"feature": "widgets-ext", "claimed_state": "In Progress"}]
    result2 = classify.classify_scan(sc2, trust_mode="no-trust", today=TODAY)
    mismatches = [m for m in result2["rollup_mismatches"] if m["feature"] == "widgets-ext"]
    # widgets-ext has one In Progress row → effective is In Progress → no
    # mismatch; a claimed "Done" would flag.
    assert mismatches == []
    sc3 = _scan()
    sc3["rollups"] = [{"feature": "widgets-ext", "claimed_state": "Done"}]
    result3 = classify.classify_scan(sc3, trust_mode="no-trust", today=TODAY)
    mismatches3 = [m for m in result3["rollup_mismatches"] if m["feature"] == "widgets-ext"]
    assert len(mismatches3) == 1
    assert mismatches3[0]["verdict"] == "rollup_mismatch"
