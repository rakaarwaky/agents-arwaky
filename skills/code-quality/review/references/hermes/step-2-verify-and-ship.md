# Step 2: Verify & Aggregate

Hermes owns the final verification and aggregation. Read Grok's per-persona files and summary, verify the aggregation is sound, and present the findings.

## 2a: Read the Artifacts

Read every per-persona review file and the summary file from the scratch dir. Cross-check:

- **Count parity**: the summary's per-persona counts must match a recount of `### Issue N — Severity: X` headings in each persona's own file. Mismatch → flag it; recount is authoritative.
- **ERROR rows**: any persona recorded `ERROR` — include it in the report with its error text, do not drop it.
- **Source untouched**: `git -C <worktree_path> status --short` must be clean (or show only the scratch-dir files, which live outside the repo) — reviewers must not have modified source. If source is dirty, report it; do not commit the dirt.

## 2b: Triage Summary

Produce a short triage for the user (your value-add, not a re-do of the per-persona files):

1. **Total issues** by severity across all personas (bugs / suggestions / nits), plus per-persona breakdown.
2. **Top issues** — the bug-severity findings most likely to matter, with their `file:line` and the persona that raised them.
3. **Cross-persona patterns** — issues raised by 2+ personas on the same file/line (corroborated findings rank higher).
4. **Errored personas** — which personas failed and why.

## 2c: Report

The per-persona files and summary stay in the scratch dir — they are deliverables, never delete them. If the user wants them out of the scratch dir, copy the summary + the persona files they asked for; do not commit them into the module repo unless explicitly asked.

## 2d: Report

Report to the user:

> Module review of <path> complete. <N>/<P> personas completed, <M> errored. <bugs> bugs, <suggestions> suggestions, <nits> nits. Top issues: ... Summary: <abs path>.

Then proceed to Step 3.
