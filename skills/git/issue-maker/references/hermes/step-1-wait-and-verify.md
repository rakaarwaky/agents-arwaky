# Step 1: Wait & Verify Gate (Hermes)

`run.py` is synchronous — when it exits, the scan → classify → open-issues pipeline is complete. Read the two-phase run report and the JSONL ledger.

## Verification Gate

1. Confirm `validate.py` exited 0 (run.py runs it at the end; check its exit code from `run.py`'s output).
2. Confirm every actionable row got one modular issue: ledger row count vs. `gh issue create` calls (unless `--dry-run`).
3. Confirm no source edits / branch / PR happened — issue-maker's invariant is "issues only."

If `validate.py` failed, report the failure verbatim and stop. If `--gh` was set, confirm each recorded issue number exists and is `OPEN` (a 403/429 rate limit is reported, never a hard failure).

Then proceed to Step 2.
