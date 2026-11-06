# Eval 1: Create from Sources

**Input:**
- Target: `references/new-tool.md`
- Sources: `config.yaml`, `scripts/deploy.sh`, existing `references/deploy-tool.md`
- Mode: `create`

**Expected:**
- New file created with all Tool definition fields (Name, Goal, Trigger, Context, Inputs, Execution, Outputs, Done condition, Error handling).
- Every fact traced to one of the three sources; no invented values.
- Any disagreement between `config.yaml` and `deploy-tool.md` logged as `CONFLICT: <A> (<src1>) vs <B> (<src2>)`.
- Output Contract includes: Deliverable, Open items, Verification, `CONFLICT:` entries. No `Removed` row (create mode).
- No file at `references/new-tool.md` existed before the run; the file is now present.

**Pass criteria:**
- All fields present and filled (no placeholders, no `UNKNOWN` without justification).
- All commands in Execution marked `VERIFIED` (ran) or `UNVERIFIED`.
- No vague references; all paths absolute or root-relative.
