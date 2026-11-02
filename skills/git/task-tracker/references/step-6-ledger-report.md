# Step 6 — ledger + report

Append one JSON object per row to `<repo-root>/docs/task-tracker-ledger.jsonl`:

```json
{"run":"YYYY-MM-DD","row":"<ROW-ID>","doc":"<source_doc>","feature":"<feature or root>","fr":["<FR-ID>"],"state":"<state>","priority":"<P0/P1/P2>","class":"<incomplete|doc_sync|unverified|fr_orphan|skip|skip_next_action|next_action_complete|next_action_pending>","proof":{"verdict":"<verdict>","evidence":"<reproduced evidence or failed check>"},"closing_condition":"<the Check from the issue's ## Closing condition — the one line that, when passed, sets this row to Done>","issue":<issue-number>,"action":"<created|commented|skipped-exists|skipped-evidence>"}
```

`action` values: `created`, `commented`, `skipped-exists`, `skipped-evidence`.
`closing_condition` is required for every row whose `action` is `created` or `commented`
— it is the condensed Check carried in the issue body; `skip` rows record `"—"`. A
verdict that arrives without a closing condition is a breach of the core invariant: it
is reported as `pending-infra` in the run report, receives no issue, and stays visible
until its condition can be stated.

Close with a count table: `rows scanned N | incomplete A | doc_sync B | unverified C |
fr_orphan D | skipped E | created X | commented Y | roll-up mismatches M | closing
conditions K | pending-infra P`.

## Run report (two-phase artifact)

The run also writes `<repo-root>/docs/task-tracker-report.json` in two phases, in
addition to the ledger:

- **Phase 1 — end of Classify.** The report file is created with the
  count-table fields (`rows_scanned`, `incomplete`, `doc_sync`,
  `unverified`, `fr_orphan`, `skipped`, `created`, `commented`,
  `rollup_mismatches`, `closing_conditions`) plus
  `actionable_verdict_count` — the count of verdicts whose verdict is in
  `{open, doc_sync, unverified, rollup_mismatch, fr_orphan, exists,
  next_action_complete, next_action_pending}` and whose
  `closing_condition` is non-empty. `created` / `commented` are `0` at
  this point; `pending_infra` and `invariant_ok` are not yet written.
- **Phase 2 — end of Issue.** The file is finalized with `pending_infra`
  (array of row ids that owe a closing condition and therefore cannot be
  issued) and `invariant_ok` (boolean), with the final `created` /
  `commented` counts and the final `actionable_verdict_count`.

A half-written file (phase 1 complete, phase 2 not) is a legitimate
intermediate state: the post-run checker below tolerates it.

## Post-run / CI gate

The machine-checkable completion gate is
`validate.py`, which re-checks the ledger and the run report without
invoking the model:

```bash
python3 <this-skill>/scripts/validate.py --repo-root <repo-root> \
    --ledger <repo-root>/docs/task-tracker-ledger.jsonl \
    --report <repo-root>/docs/task-tracker-report.json [--gh]
```

Without `--gh`, the open-issue liveness criterion is reported as
`deferred-to-gh`: exit 0 means every row is classified, every actionable
row has a recorded issue number, and the invariants hold offline — it does
**not** imply the recorded issues are still open on GitHub. Pass `--gh`
(with valid `gh` auth, e.g. `GH_TOKEN` in CI) to also confirm each ledger
issue number exists and is `OPEN`.

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

## Personas

The workflow ships as `workflows/task-tracker.rhai` in this repo, runnable as
`/task-tracker <repo-root>` once `~/.grok` symlinks resolve to this tree. It drives
the four personas, defined in `personas/task-tracker-*.toml`:

| Persona | Capability | Role |
| --- | --- | --- |
| `task-tracker-scanner` | read-only | one per feature: state table + rows + FR set + roll-up row as JSON |
| `task-tracker-classifier` | read-only | zero-trust buckets, effective state per feature, orphan flags |
| `task-tracker-verifier` | read-only (source files + tests + `gh release view` only) | re-runs cited gates, re-checks hashes, confirms release evidence, dedupe, verdicts |
| `task-tracker-issuer` | write (GitHub issues only) | creates / comments issues; every body carries one `## Closing condition` |

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
