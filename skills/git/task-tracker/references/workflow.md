# Workflow

### Step 1 — discover features

Enumerate feature directories (`modules/`, `packages/`, `crates/` — whichever exist) and
the root spec docs. One discovery agent; output is a feature table:

```json
{"root": ["ROADMAP.md", "BACKLOG.md"], "features": [
  {"name": "tools", "dir": "modules/tools", "docs": ["modules/tools/FRD.md", "modules/tools/BACKLOG.md"]},
  {"name": "skills", "dir": "modules/skills", "docs": ["modules/skills/FRD.md", "modules/skills/BACKLOG.md"]}
]}
```

Also record the repo's State Definitions vocabulary per doc so later phases quote the
right state names.

### Step 2 — spawn one scanner subagent per feature

**Default path: run the deterministic scanner script** (no LLM subagent; one
host call per run, matching the workflow's script path):

```bash
python3 <this-skill>/scripts/scan.py --repo-root <repo-root> --discovery <discovery.json>
```

`<discovery.json>` is the Step-1 discovery output written to a temp file. The
script parses every in-scope doc's State Definitions table, row tables,
Next Action / Item cells (cell value only — prose outside the table is out
of scope), FR-id sets, and roll-up rows into one ScanOutput JSON. A
non-zero exit is a hard stop: fix the scanner and re-run; the workflow does
**not** fall back to an LLM scanner.

**`--legacy` path (rollback escape):** one read-only scanner subagent per
feature plus one for `root`. A feature scanner owns its feature's whole doc
set plus the roadmap roll-up row for that feature; it must not read other
features' docs. Splitting by feature keeps every FR ID and its backlog
equivalent in one agent's context, which is what makes the orphan check
possible. The scanner prompt (verbatim cell-value constraint for the Next
Action cell) and output shape are the legacy form:

```text
You are a read-only scanner for the feature "<feature>" in <repo-root>.
Read each of these files in full: <abs paths>.
1. Extract each file's State Definitions table; list the state names it defines. If a
   file has none, note that and continue — rows still count.
2. Extract every table row whose headers include ID (or Feature / Branch) and State.
   Also capture the doc-level "State: <value>" line at the top of a feature backlog.
3. Extract the FR ID set this feature owns: every FR-<SCOPE>-NNN declared in its FRD,
   and every FRD Ref cell in its backlog rows.
4. If the roadmap has a Feature Roll-up table, extract this feature's roll-up row
   verbatim (all cells, including State, Health, Next, Updated).
5. For each task row output one JSON object:
   {"id":"<row id>","title":"<item text>","state":"<verbatim state>","priority":"<P0/P1/P2 or —>","health":"<health or —>","fr_refs":["<FR-…>"],"source_doc":"<repo-relative doc path>","row_text":"<verbatim row text>"}
   State must appear in the source row verbatim. Do not infer, fill in, or normalize
   state values. A row without a state column value is {"id":...,"state":"unknown"}.
6. Also output the FR set:
   {"fr_declared":["FR-…"],"fr_referenced":["FR-…"],"rollup_row":"<verbatim row or null>"}
7. Return {"rows":[…],"fr":{…}}. An empty rows array is valid only after reading every
   file in full.
```

Wait on all handles. Collect rows; dedupe on `(id, source_doc)`.

### Step 3 — classify with zero trust

**Default path: run the deterministic classifier script** on the scanner's
ScanOutput JSON (no LLM, no inline re-derivation of the classification
table):

```bash
python3 <this-skill>/scripts/classify.py --repo-root <repo-root> \
    --scan-out <scan.json> --trust-mode <no-trust|trust>
```

The script applies the doc-determinable part of the classification table:
state bucketing, the Next Action word-count skip rule, per-feature
effective-state ranking, FR-orphan detection, roll-up mismatch detection,
and the `next_action_pending` / `next_action_complete` closing-condition
strings. Every other verdict leaves `closing_condition: null` for the LLM
verifier to fill in. A non-zero exit is a hard stop — fix the classifier
and re-run; there is no fallback to inline logic.

**`--legacy` path (rollback escape):** apply the classification table
locally (the workflow's inline Rhai logic).

Either way, every `Done` row goes to the verifier as a **proof demand** in
`--no-trust` mode, not as a skip candidate. A row whose `Updated` date is
older than 14 days is a staleness flag; the verifier re-reads the code
regardless.

Compute the per-feature effective state here (the script does this), before
verification, so the verifier can compare it against the roll-up claim.

### Step 4 — verify (read-only, mandatory for every row)

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
| `skip_next_action` | Next Action contains `none` or `<skip>` | ledger only, no issue |
| `next_action_complete` | Next Action item already implemented in code + tests | `[DOC-SYNC]` issue: set Next Action to `none` |
| `next_action_pending` | Next Action item not yet implemented | tracking issue: implement the action, then set Next Action to `done` |

### Step 5 — open modular issues

One row, one issue. A row whose `Next Action` or `Item` text lists two or more
independent deliverables (separable by a semicolon / comma with distinct objects)
splits into one issue per deliverable; each split issue carries the parent row id in
its title and lists the siblings in its body.

**Title format**

```text
[BACKLOG] <ROW-ID> — <one-line task summary>        # root rows
[<feature>] <ROW-ID> — <one-line task summary>       # feature-scoped rows
[DOC-SYNC] <ROW-ID> — <doc path> still reports <stale or unproven state>
[DOC-SYNC] <feature> roll-up — claims <state>, backlog says <effective state>
[DOC-SYNC] <feature> FR <FR-ID> — has no backlog row   # fr_orphan
```

The feature tag is the lowercase directory name of the owning feature (e.g. `browser`,
`cli`, `api`, `compositor`); for Rust workspaces use the crate name.

**Body**

````markdown
Source: `<source_doc>` · row `<ROW-ID>` · scanned by `/task-tracker` on `<date>`

| Field | Value |
| --- | --- |
| State (doc) | <verbatim state> |
| Priority | <P0/P1/P2 or —> |
| Health | <health or —> |
| Owner | <owner or —> |
| Target | <target date or —> |
| Classification | incomplete / doc_sync / unverified / fr_orphan |

## Task
<verbatim Next Action / Item text>

## Evidence in doc
> <verbatim Actual Condition / row text>

## Verification
<the file paths and line ranges read, and whether the code confirms or contradicts the row's claim>

## Roll-up check
<feature>: roll-up claims <state>; backlog effective state <effective state>;
offending rows: <ROW-ID> (<state>), …

## Closing condition
**Check:** <file paths> must implement <the row's described behavior> and be exercised by
<test path>; `<test command>` must pass.
<# the one-line verdict-specific check, per the Closing contract table>

**Advance:** when the check passes, set row `<ROW-ID>` `State` to `Done` in `<source_doc>`
and write the commit SHA + the `<test command>` output into its evidence cell. Every FR ID
cited by the row carries to `Done` with it — the FR is evidenced by its backlog rows, so
this row's advance is the FR's advance.

**Proof:** close this issue with the commit link and the command output. No proof, no
close, no `Done`.

## Tracking only
This issue tracks the task. Implementation lands in its own PR. The `## Closing condition`
above is the only path to `Done`: its check passes, the row advances in `<source_doc>`,
and this issue closes with the proof. For a `[DOC-SYNC]` issue, the fix is the document
edit aligning the state with reality — that edit is both the check and the advance.
````

**Labels** (create on first use, then reuse): `task-tracker`, one `state:<doc-state>`
(`state:ready`, `state:in-progress`, `state:in-review`, `state:done`), one of
`p0` / `p1` / `p2`, plus `doc-sync` for the `doc_sync`, `unverified`,
`rollup_mismatch`, and `fr_orphan` classes. No other labels — the four title formats
and this label set are the whole vocabulary.

**Dry run**: the default run is live — steps 1–6 all execute and issues are created.
Passing `--dry-run` executes steps 1–4 and prints every would-be title, body (including
its `## Closing condition`), and label without calling `gh issue create`.

### Step 6 — ledger + report

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

**Run report (two-phase artifact).** The run also writes
`<repo-root>/docs/task-tracker-report.json` in two phases, in addition to
the ledger:

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

**Post-run / CI gate.** The machine-checkable completion gate is
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
