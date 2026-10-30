"""Closing-condition string templates for task-tracker verdicts.

The templates here are the single source of truth (SSOT) for the
closing-condition strings that are fully determinable from the scan JSON.
Verdicts owned by the LLM verifier (fr_orphan, rollup_mismatch, doc_sync,
unverified, open) leave closing_condition null in classify.py output and
let the verifier fill in a check that names the files it actually read.

Stdlib only.
"""

from __future__ import annotations

# next_action_pending: the action is not yet implemented; the check names the
# source paths, the test, the verification command, and the doc advance.
NEXT_ACTION_PENDING_TEMPLATE = (
    "{feature}/src/ implements {action_description}, exercised by "
    "{feature}/tests/{test_file}; {test_command} passes; then set row "
    "{row_id} Next Action to \"done\" in {source_doc}."
)

# next_action_complete: the action is already verified in code + tests;
# the check is the doc edit that clears the Next Action cell.
NEXT_ACTION_COMPLETE_TEMPLATE = (
    "Set row {row_id} Next Action to \"none\" in {source_doc} "
    "(action already verified in code + tests)."
)

# skip_next_action: no issue is created; the ledger records the skip.
SKIP_NEXT_ACTION_TEMPLATE = "—"


def closing_condition_next_action_pending(
    feature: str,
    row_id: str,
    action_description: str,
    test_file: str,
    test_command: str,
    source_doc: str,
) -> str:
    """Build the closing condition for a next_action_pending verdict."""
    return NEXT_ACTION_PENDING_TEMPLATE.format(
        feature=feature,
        row_id=row_id,
        action_description=action_description,
        test_file=test_file,
        test_command=test_command,
        source_doc=source_doc,
    )


def closing_condition_next_action_complete(
    row_id: str,
    source_doc: str,
) -> str:
    """Build the closing condition for a next_action_complete verdict."""
    return NEXT_ACTION_COMPLETE_TEMPLATE.format(row_id=row_id, source_doc=source_doc)


def closing_condition_skip_next_action() -> str:
    """Closing condition recorded for skip_next_action rows (no issue)."""
    return SKIP_NEXT_ACTION_TEMPLATE
