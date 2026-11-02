# Step 4 — verify (read-only, mandatory for every row)

There is no skip path that avoids this step. The verifier:

1. For each row in the feature's backlog, reads the row's item text and Actual Condition.
2. Opens the files under `<feature>/src/` and `<feature>/tests/` that the row refers to.
3. Confirms the described behavior is implemented and tested.

Verdicts:

| Verdict | Meaning | Action |
| --- | --- | --- |
| `open` | code does not implement it, no existing tracking issue | create a tracking issue |
| `doc_sync` | code implements it, doc says otherwise | create a `[DOC-SYNC]` issue |
| `unverified` | Done claim, code does not match | create a `[DOC-SYNC]` issue naming the failed check |
| `skip` | Done, code fully confirms it with command + commit evidence (no-trust mode) | ledger only, evidence recorded |
| `skip` | Done row accepted under `--trust` mode without code verification | ledger only |
| `fr_orphan` | FR id with no backlog row | tracking issue on the feature |
| `skip_next_action` | Next Action column present; cell empty, `none`, or `<skip>` | ledger only, no issue (rows with no Next Action column classify by state instead) |
| `next_action_complete` | Next Action item already implemented in code + tests | `[DOC-SYNC]` issue: set Next Action to `none` |
| `next_action_pending` | Next Action item not yet implemented | tracking issue: implement the action, then set Next Action to `done` |
