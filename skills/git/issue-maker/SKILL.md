---
name: issue-maker
description: "repo → issues: zero-trust issue maker that maps AES spec documents (PRD, ROADMAP, BACKLOG, FRD, DESIGN, plus module and package feature docs) into modular GitHub tracking issues. Done rows are re-verified against live source and test evidence. Every issue carries a closing-condition that advances its ROW and all FR IDs to Done. Never opens a PR — issues only. Hermes runs the audit driver via terminal (stdlib scripts, no subagent); no source edits, no branches, no PRs — nothing to delegate to Grok."
when-to-use: /issue-maker — map incomplete tasks to GitHub issues (repo → issues), create tracking issues from ROADMAP or BACKLOG, verify Done claims against code, ensure every issue carries a closing-condition that advances the roadmap state to Done. Outputs GitHub issues only; never edits source, never creates a branch, never opens a PR.
argument-hint: <repo-root> [--discovery <json>] [--scan-out <json>] [--classify-out <json>] [--trust-mode <no-trust|trust>] [--dry-run] [--ledger <path>] [--report <path>] [--legacy]---

# Issue Maker — repo → issues: zero-trust spec audit → modular GitHub tracking issues with closing conditions

One run covers one repo. It reads the spec-document states, **proves** which rows are real work and which are fiction, and opens a modular issue per finding. **Direction: repo → issues only.** The run outputs GitHub issues only. It never edits source code, never creates a branch, never opens a PR. Every issue it opens carries one closing condition: the check whose fulfillment advances that issue's row to `Done` in its source document.

## Global Rules

Rules that apply to every issue-maker run. Scripts and reference files cite these; they never restate them.

- **Zero trust**: Never trusts any doc claim — Done rows are re-verified against live source and test evidence.
- **Issues only**: The run outputs GitHub issues only. Never edits source code, never creates a branch, never opens a PR.
- **One closing condition per issue**: Every issue carries exactly one `## Closing condition` whose fulfillment advances that issue's row to `Done` in its source document. No issue is counted as created until its closing condition is present in the body.
- **Invariant**: Fixing ALL open issues equals ALL FR states = Done. Every row from every in-scope doc appears in the ledger with a class.
- **Scripts**: All scripts live under `scripts/`, are stdlib-only Python (no `uv sync`, no third-party deps), and are CI-gated.
- **Completion gate**: `validate.py` exits 0 against the ledger (and the run report when present): `python3 <this-skill>/scripts/validate.py --repo-root <repo> --ledger <repo>/docs/task-tracker-ledger.jsonl --report <repo>/docs/task-tracker-report.json` (artifact filenames unchanged by the skill rename).
- **Offline vs --gh**: Without `--gh`, the open-issue liveness criterion is reported `deferred-to-gh` — exit 0 does not imply the full GitHub-facing contract held. `--gh` confirms each ledger issue exists and is `OPEN`; a 403/429 rate limit is reported, never a hard failure.

## Routing

The lane is determined from a physical signal, not by self-identification. Each agent's launcher stamps a fixed attribution env var into every command it runs; the model cannot set these.

```bash
if [[ -n "${HERMES_AGENT:-}" ]]; then echo HERMES
elif [[ -n "${GROK_AGENT:-}" ]]; then echo GROK
else echo UNSET; fi
```

- `HERMES` → **Hermes lane.** Read `references/hermes/` (Steps 0–2). Stop.
- `GROK` → **Grok lane.** Read `references/grok/` (auxiliary recipes, Steps 0–6). Stop.
- `UNSET` → stop and report. Do not guess the lane.

Marker provenance:

- **Hermes** re-exports `AI_AGENT=hermes-agent` and `HERMES_AGENT=true` on every command.
- **Grok Build** runs with `GROK_AGENT=1`.

Read only the winning lane's references. Do not read the other lane's. The Grok lane is auxiliary only — issue-maker itself never enters it; a coding task launched from an issue-maker finding is a different skill's run.

### Hermes lane (Steps 0–2)

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| 0 | [`references/hermes/step-0-plan-and-authorize.md`](references/hermes/step-0-plan-and-authorize.md) | Scope decision (trust mode, ledger/report paths, `--gh`), GitHub auth check, Hermes lane entry via `run.py` |
| 1 | [`references/hermes/step-1-wait-and-verify.md`](references/hermes/step-1-wait-and-verify.md) | Wait for `run.py`; verify gate — `validate.py` exit 0, issues opened vs ledger rows, issues-only invariant |
| 2 | [`references/hermes/step-2-final-report.md`](references/hermes/step-2-final-report.md) | Final report: rows, classes, issues opened (or dry-run deferred), closing conditions, `--gh` liveness, invariant result |

### Grok lane (auxiliary recipes)

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| 0 | [`references/grok/step-0-discovery-scope.md`](references/grok/step-0-discovery-scope.md) | Spec-doc scope discovery, the three state-source layouts, and the feature/FR model. |
| 1 | [`references/grok/step-1-discover-features.md`](references/grok/step-1-discover-features.md) | Enumerate feature directories and root spec docs into a discovery table. |
| 2 | [`references/grok/step-2-scan.md`](references/grok/step-2-scan.md) | Run `scan.py` (default) or the legacy read-only scanner subagent per feature (`--legacy`). |
| 3 | [`references/grok/step-3-classify.md`](references/grok/step-3-classify.md) | Trust modes, Next Action handling, zero-trust policy, state vocabulary, classification, evidence, roll-up reconciliation; run `classify.py`. |
| 4 | [`references/grok/step-4-verify.md`](references/grok/step-4-verify.md) | Read-only verification of every row; verdicts. |
| 5 | [`references/grok/step-5-open-issues.md`](references/grok/step-5-open-issues.md) | One modular issue per row: title, body, labels, dry-run. |
| 6 | [`references/grok/step-6-ledger-report.md`](references/grok/step-6-ledger-report.md) | Ledger + two-phase run report, scripts, personas, completion criteria, and the `validate.py` CI gate. |

Note: the scanner-subagent mentions in `references/grok/step-2-scan.md` are rollback-escape `--legacy` recipes only; the default path runs the deterministic `scan.py` script (stdlib, no subagent).

