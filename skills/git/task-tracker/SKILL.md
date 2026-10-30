---
name: task-tracker
description: >
  Zero-trust task tracker: maps AES spec documents (PRD, ROADMAP, BACKLOG, FRD, DESIGN,
  plus module and package feature docs) into modular GitHub tracking issues. Never trusts
  any doc claim — Done rows are re-verified against live source and test evidence.
  Every issue created carries a closing-condition that, when fulfilled, advances the ROW
  and ALL ITS FR IDs to Done. The intended invariant: fixing ALL open issues equals
  ALL FR states = Done. Use when the user runs /task-tracker, asks to map backlog tasks
  to GitHub issues, or asks for a zero-trust audit of spec states.
when-to-use: >
  /task-tracker, map incomplete tasks to GitHub issues, create tracking issues from
  ROADMAP or BACKLOG, verify Done claims against code, ensure every issue carries
  a closing-condition that advances the roadmap state to Done.
argument-hint: <repo-root> [--dry-run] [--trust | --no-trust] [--legacy]
---

# Task Tracker — zero-trust spec audit → modular GitHub tracking issues with closing conditions

One run covers one repo. It reads the spec-document states, **proves** which rows are
real work and which are fiction, and opens a modular issue per finding. The run outputs
GitHub issues only. It never edits source code, never creates a branch, never opens a
PR. Every issue it opens carries one closing condition: the check whose fulfillment
advances that issue's row to `Done` in its source document.

## Scenarios

| Scenario | Reference |
| --- | --- |
| Trust modes, Next Action handling, zero-trust policy, state vocabulary, classification, evidence, roll-up | [`references/classification-and-trust.md`](references/classification-and-trust.md) |
| Spec-doc scope discovery and the two state-source layouts | [`references/discovery-and-scope.md`](references/discovery-and-scope.md) |
| Full workflow pipeline | [`references/workflow.md`](references/workflow.md) |

The `classification-and-trust.md` file holds the long-form prose sections for trust
modes, zero-trust policy, scope, state vocabulary, classification tables, evidence
rules, and roll-up reconciliation. The `discovery-and-scope.md` file holds scope
discovery, state sources, and the feature model. The `workflow.md` file holds the
Step 1 → Step 6 pipeline and personas.

## Scripts

All scripts live under `<this-skill>/scripts/`, are stdlib-only Python
(no `uv sync`, no third-party deps), and are CI-gated.

| Script | What it does | Invocation |
| --- | --- | --- |
| `scan.py` | Deterministic scanner: parses the in-scope spec docs named by the discovery JSON into a ScanOutput JSON (rows with verbatim state + Next Action cell value, FR-id sets, roll-up row). Replaces the per-feature LLM scanner subagents. | `python3 scripts/scan.py --repo-root <repo> --discovery <discovery.json> [--features f1 f2] [--out <path>]` |
| `classify.py` | Deterministic classifier: ScanOutput + `--trust-mode` → per-row pre-verifier buckets, effective state, FR orphans, roll-up mismatches, staleness flags, and the doc-determinable closing-condition strings. | `python3 scripts/classify.py --repo-root <repo> --scan-out <scan.json> --trust-mode <no-trust\|trust> [--out <path>]` |
| `validate.py` | Post-run invariant checker and CI gate: ledger shape, closing-condition re-runnability, skip evidence, issue-number population, invariant count, run-report artifact; optional `--gh` liveness check. | `python3 scripts/validate.py --repo-root <repo> --ledger <ledger.jsonl> [--report <report.json>] [--gh] [--out <path>]` |
| `cache.py` | XDG discovery/scan cache keyed on `sha256(content)` of each spec doc, so unchanged docs skip re-scanning; `--check` / `--refresh`. | `python3 scripts/cache.py --repo-root <repo> --discovery <discovery.json> [--check\|--refresh]` |
| `ledger.py` | JSONL ledger reader/writer utilities and the shared `verify_ledger_invariants` engine behind `validate.py` checks 1–4. | `python3 scripts/ledger.py <subcommand>` |

Offline vs `--gh` boundary (validate.py): without `--gh`, the open-issue
liveness criterion is reported `deferred-to-gh` — exit 0 does not imply
the full GitHub-facing contract held; the recorded issue numbers are
structurally checked only. `--gh` (opt-in, requires valid `gh` auth /
`GH_TOKEN` in CI) confirms each ledger issue exists and is `OPEN`; a
403/429 rate limit is reported, never a hard failure.

## Completion criteria

- [ ] Every row from every in-scope doc appears in the ledger with a class.
- [ ] Every `incomplete` row maps to exactly one open issue (created, commented, or pre-existing).
- [ ] Every `doc_sync` and every `unverified` row maps to an open `[DOC-SYNC]` issue.
- [ ] Every `Done` row shows code evidence (file + line + test) in the ledger, or is `unverified`.
- [ ] Every feature roll-up row is reconciled against its backlog; each mismatch is an issue.
- [ ] Every FR ID declared in an FRD has a cited backlog equivalent, or is an `fr_orphan` issue.
- [ ] No `skip` row dropped silently — each has its reproduced evidence cited in the ledger.
- [ ] Every created, commented, and dry-run issue carries exactly one `## Closing condition` whose Advance sets its row to `Done` in the source doc, and the ledger records its Check.
- [ ] No issue is counted as created until its `## Closing condition` is present in the body.
- [ ] No file changed outside `docs/task-tracker-ledger.jsonl` and `docs/task-tracker-report.json` (the two-phase run report described in Step 6).
- [ ] `validate.py` exits 0 against the ledger (and the run report when present): `python3 <this-skill>/scripts/validate.py --repo-root <repo> --ledger <repo>/docs/task-tracker-ledger.jsonl --report <repo>/docs/task-tracker-report.json` — the machine-checkable completion gate.
- [ ] No branch, PR, or code change created.
