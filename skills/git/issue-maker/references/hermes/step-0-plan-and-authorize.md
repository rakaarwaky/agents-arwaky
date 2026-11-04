# Step 0: Plan & Authorize (Hermes)

Hermes owns the audit plan — which spec docs are in scope, the trust mode, the ledger/report paths, and GitHub auth. This is coordination, not coding.

## 0a: Scope Decision

From the argument hint `<repo-root> [--discovery <json>] [...]` resolve:

- `<repo-root>` — absolute path; must be a git checkout with spec docs present.
- `--discovery <json>`, `--scan-out <json>`, `--classify-out <json>` — optional override paths; default to `docs/task-tracker-*.json` next to `<repo-root>/docs/task-tracker-ledger.jsonl` when `--ledger` is set.
- `--trust-mode <no-trust|trust>` (default `no-trust` per the skill's invariant).
- `--dry-run` — do not call `gh issue create`, still write ledger + report.
- `--ledger <path>` / `--report <path>` — defaults unchanged by skill rename (`docs/task-tracker-ledger.jsonl`, `docs/task-tracker-report.json`).
- `--gh` — opt-in GitHub liveness check.

## 0b: Auth Check (Hermes)

When `--gh` is set, confirm `gh auth status` before spawning anything; report `CONNECTION_REQUIRED` if not authenticated. Without `--gh`, open-issue liveness is reported `deferred-to-gh`.

## 0c: Hermes Lane Entry

The Hermes lane runs the audit driver itself via terminal (stdlib scripts, no LLM subagent, no Orca worktree):

```
python3 <this-skill>/scripts/run.py --repo-root <repo-root> [--discovery ...] [--scan-out ...] [--classify-out ...] [--trust-mode ...] [--dry-run] [--ledger ...] [--report ...] [--legacy] [--gh]
```

This is Hermes invoking its own repo scripts — not a subagent. After `run.py` exits, proceed to Step 1.

Report: "issue-maker audit planned: repo=<repo-root>, trust-mode=<no-trust|trust>, dry-run=<yes|no>, gh=<yes|no>."
