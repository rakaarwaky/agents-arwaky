---
name: task-tracker
description: >
  Zero-trust task tracker: maps AES spec documents (PRD, ROADMAP, BACKLOG, FRD, DESIGN,
  plus module and package feature docs) into modular, deduplicated GitHub tracking
  issues. Never trusts any doc claim — Done, QA, and Released rows are re-verified
  against live git and GitHub evidence exactly like incomplete rows. Splits work into
  one subagent per feature, keyed by the FR IDs each feature owns (every FR ID in a
  roadmap or FRD has a backlog equivalent), double-checks the ROADMAP feature roll-up
  against each feature's backlog reality, and opens one issue per finding — tracking
  only, with no implementation. Use when the user runs /task-tracker, asks to map
  backlog tasks to GitHub issues, or asks for doc-sync tracking.
when-to-use: >
  /task-tracker, map incomplete tasks to GitHub issues, create tracking issues from
  ROADMAP or BACKLOG, audit document states against reality, doc-sync issues for stale
  spec documents, verify Done/QA claims in a roadmap
argument-hint: <repo-root> [--dry-run] [--state-label task-tracker] [--no-trust-doc]
---

# Task Tracker — zero-trust spec audit → modular GitHub tracking issues

One run covers one repo. It reads the spec-document states, **proves** which rows are
real work and which are fiction, and opens a modular issue per finding. The run outputs
GitHub issues only. It never edits source code, never creates a branch, never opens a
PR.

## Zero-trust policy (read first)

No state value in any spec document is trusted. A row marked `Done`, `QA`, or
`Released` is a **claim**, never a fact. Every row — whatever its state — is verified
against live evidence before it is allowed to be skipped:

- A `Done` row owes proof that the described behavior is actually implemented in the feature's current source code (`<feature>/src/`) and exercised by at least one test in `<feature>/tests/`.
- A `Released` row owes proof that the described behavior is implemented AND the feature's code shows no pending work for it; a release tag in the doc's evidence cell is not proof.
- A `QA` / `In Review` row owes the fr row it leans on; the row stays `incomplete` and
  the tracker checks whether the work has since landed by reading the actual source, not by checking for a merged PR.
- Evidence that does not reproduce flips the row to `unverified` and produces a
  `[DOC-SYNC]` issue. The doc never gets the benefit of the doubt.

The roll-up gets the same treatment: the ROADMAP `Feature Roll-up` row for a feature is
reconciled against the **actual** state of that feature's backlog rows — a roll-up that
says `Done` while any backlog row is still `QA` or `In Progress` is a mismatch and
becomes a `[DOC-SYNC]` issue.

When `--no-trust-doc` is passed, even the scan step may not treat a doc's State
Definitions table as authoritative until the verifier has confirmed the doc is not a
template or scratch file (see Scope).

## Scope

The skill is repo-agnostic: any AES-architecture repo that keeps spec documents inside
the repo tree works. Discover scope at run time with the two rules below; do not
assume a layout.

**In scope** — any `.md` that either:
1. Contains a `## State Definitions` or `### State definitions` heading (the authoritative vocabulary table), or
2. Is a feature `BACKLOG.md`, `FRD.md`, or `DESIGN.md` listed by the root spec docs, or sits under a feature directory (`modules/`, `packages/`, `crates/`) and has a row table whose headers include `ID` (or `Feature` / `Branch`) and `State`.

**Out of scope** — any path whose first segment after the repo root starts with a dot
(`.git/`, `.agents/`, `.grok/`, `.venv/`, `.tox/`, `.pytest_cache/`, `.mypy_cache/`,
`.ruff_cache/`, `.idea/`, `.vscode/`, and any other dot-prefixed directory) —
dot-prefixed directories are always scratch, session, or tooling, never spec docs.
Also exclude build and template paths matching `node_modules|target|dist|__pycache__|htmlcov|coverage|junit|vendor|skills|references|workspaces-bad|workspaces-good`.

Prompt scratch files and skill reference templates quote the words "State Definitions"
without being specs — never include them.

## State sources

Two common layouts, both in scope:

| Shape | Where the state lives |
| --- | --- |
| Roadmap-owned | `ROADMAP.md` (or `ROADMAP.md`/`DESIGN.md` at root) holds the definitions, a backlog table, a phase plan, and a feature roll-up; feature `BACKLOG.md` files carry only their own row table |
| Backlog-owned | Root `BACKLOG.md` holds the definitions (`### State definitions`), the feature index, the roll-up, and the root row table; each feature `BACKLOG.md` declares its own doc-level `State: <value>` line plus its row table |

In the backlog-owned shape the doc-level `State:` line at the top of a feature backlog
is a real classification target in its own right — a feature still `In Progress` or
`Idea` while its row table is empty produces a tracking issue for the feature roll-up
row, not for the vanished rows.

If the repo uses neither shape exactly, follow the discovery rule and extract every
table that has both an ID (or Feature) column and a State column.

## State vocabulary

The five base states every AES repo carries:

| State | Meaning |
| --- | --- |
| Idea | Not examined; no spec. |
| Refinement | Being specced. |
| Ready | Specified; not started. |
| In Progress | Active now. |
| Blocked | Name the blocker in Actual Condition. |

Extended states seen in some repos: `In Review`, `QA`, `Done`, `Released`, `Deferred`.
The authoritative table for the current repo is its own State Definitions table —
parse it, do not assume the full vocabulary.

## Feature model

A **feature** is a directory under `modules/`, `packages/`, or `crates/` (whichever the
repo has). Root-level spec docs form one extra group, `root`.

Every feature owns a set of **FR IDs** — the requirement ids declared in its `FRD.md`
(`FR-<SCOPE>-001`) and referenced by its backlog rows. Every FR ID in a roadmap or FRD
has a backlog equivalent: a row whose `FRD Ref` cell cites that id. The tracker treats
the feature as the unit of work, and every FR ID in the feature is checked both ways:

- **FR → backlog**: each FR ID declared in the FRD must appear in at least one backlog
  row's `FRD Ref`. An FR with no backlog row is a `fr_orphan` finding.
- **backlog → FR**: each `FRD Ref` in a backlog row must resolve to an FR ID declared
  in the FRD. A dangling reference is a `fr_orphan` finding.

## Classification (every row, zero trust)

| Row state | Classification | Action |
| --- | --- | --- |
| Idea, Refinement, Ready, In Progress, Blocked | `incomplete` | tracking issue |
| In Review, QA | `incomplete` | tracking issue, body notes the current gate |
| Deferred | `incomplete` | tracking issue, label `deferred`, body carries the reason |
| Done / Released whose claimed behavior is confirmed present in the feature's current source code and exercised by at least one test | `skip` | no issue, ledger records the reproduced evidence |
| Done / Released claim where the described behavior is absent, incomplete, or untested in the feature's source tree | `unverified` | `[DOC-SYNC]` issue demanding proof |
| Any incomplete state where the work is present and tested in the source code but the doc still reports an incomplete state | `doc_sync` | doc-update issue |
| FR ID declared in FRD with no backlog row (or vice versa) | `fr_orphan` | tracking issue on the feature |

There is no path where a `Done` or `Released` marker alone suppresses an issue. Doc
text is the hypothesis; live evidence is the verdict.

### Evidence rules

| Claim shape | Verification |
| --- | --- |
| behavior described in row | locate the implementing file under `<feature>/src/`; confirm the described function/flag/class/config exists and its logic matches the claim |
| test coverage claimed | locate the test in `<feature>/tests/`; confirm it exercises the described behavior and is not a trivial or disabled test |
| commit hash in row | hash is NOT proof; ignore it and verify the code directly |
| merged PR number in row | PR number is NOT proof; verify the code directly |
| release tag in row | tag is NOT proof; verify the code directly |

The verifier reads source files, not git history. A hash, PR number, or tag cited in a row is context, not evidence.

### Roll-up double-check

For every `Feature Roll-up` row (roadmap-owned shape) or feature index row
(backlog-owned shape), the verifier recomputes the feature's **effective state** from
its backlog rows:

1. Collect every backlog row of the feature plus its doc-level `State:` line.
2. Effective state = the worst state present, ranked:
   `Blocked` > `In Progress` > `Refinement` > `Ready` > `Idea` > `QA` > `In Review` > `Deferred` > `Done` > `Released`.
   Any non-`Done` row makes the feature non-`Done`; `QA` never rolls up to `Done`.
3. If the roll-up row's `State` claims `Done` or `Released` while the effective state
   is anything less, open `[DOC-SYNC]` on the roll-up row with the offending backlog
   row ids and states listed in the body.
4. If the roll-up claims `Done` and the effective state is `Done`, still re-verify each
   contributing backlog row's evidence per the Evidence rules table — a roll-up is only
   as good as the rows it aggregates.
5. Symmetric check: a feature whose roll-up says `QA` while every backlog row is
   verified `Done` with reproducing evidence is also a mismatch (under-claimed), and
   becomes a `[DOC-SYNC]` issue.

The same reconciliation runs on the doc-level `State:` line of a backlog-owned feature
backlog.

## Workflow

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

One subagent per feature, plus one for `root`. A feature scanner owns its feature's
whole doc set plus the roadmap roll-up row for that feature; it must not read other
features' docs. Splitting by feature keeps every FR ID and its backlog equivalent in
one agent's context, which is what makes the orphan check possible.

Scanner prompt, self-contained:

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

Apply the classification table locally. Every `Done` / `Released` / `QA`-gate row goes
to the verifier as a **proof demand**, not as a skip candidate. A row whose `Updated`
date is older than 14 days is a staleness flag; the verifier re-reads the code regardless.

Compute the per-feature effective state here, before verification, so the verifier can
compare it against the roll-up claim.

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
| `unverified` | Done/Released claim, code does not match | create a `[DOC-SYNC]` issue naming the failed check |
| `skip` | Done/Released, code fully confirms it | ledger only, evidence recorded |
| `fr_orphan` | FR id with no backlog row | tracking issue on the feature |

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

## Tracking only
This issue tracks the task. Implementation lands in its own PR and closes this
issue with verification evidence (commit + command output). For a `[DOC-SYNC]`
issue, the fix is the document edit aligning the state with reality, plus the
reproduced evidence that justifies the new state.
````

**Labels** (create on first use, then reuse): `task-tracker`, one `state:<doc-state>`,
one of `p0` / `p1` / `p2`, plus `doc-sync` for the `doc_sync`, `unverified`,
`rollup_mismatch`, and `fr_orphan` classes, and `deferred` for Deferred rows. No other
labels — the four title formats and this label set are the whole vocabulary.

**Dry run**: `--dry-run` executes steps 1–4 and prints every would-be title, body, and
label without calling `gh issue create`.

### Step 6 — ledger + report

Append one JSON object per row to `<repo-root>/docs/task-tracker-ledger.jsonl`:

```json
{"run":"YYYY-MM-DD","row":"<ROW-ID>","doc":"<source_doc>","feature":"<feature or root>","fr":["<FR-ID>"],"state":"<state>","priority":"<P0/P1/P2>","class":"<incomplete|doc_sync|unverified|fr_orphan|skip>","proof":{"verdict":"<verdict>","evidence":"<reproduced evidence or failed check>"},"issue":<issue-number>,"action":"<created|commented|skipped-exists|skipped-evidence>"}
```

`action` values: `created`, `commented`, `skipped-exists`, `skipped-evidence`.

Close with a count table: `rows scanned N | incomplete A | doc_sync B | unverified C |
fr_orphan D | skipped E | created X | commented Y | roll-up mismatches M`.

## Personas

The workflow ships as `workflows/task-tracker.rhai` in this repo, runnable as
`/task-tracker <repo-root>` once `~/.grok` symlinks resolve to this tree. It drives
the four personas, defined in `personas/task-tracker-*.toml`:

| Persona | Capability | Role |
| --- | --- | --- |
| `task-tracker-scanner` | read-only | one per feature: state table + rows + FR set + roll-up row as JSON |
| `task-tracker-classifier` | read-only | zero-trust buckets, effective state per feature, orphan flags |
| `task-tracker-verifier` | read-only (source files + tests only) | re-runs cited gates, re-checks hashes, dedupe, verdicts |
| `task-tracker-issuer` | write (GitHub issues only) | creates / comments issues |

## Completion criteria

- [ ] Every row from every in-scope doc appears in the ledger with a class.
- [ ] Every `incomplete` row maps to exactly one open issue (created, commented, or pre-existing).
- [ ] Every `doc_sync` and every `unverified` row maps to an open `[DOC-SYNC]` issue.
- [ ] Every `Done` / `Released` row shows code evidence (file + line + test) in the ledger, or is `unverified`.
- [ ] Every feature roll-up row is reconciled against its backlog; each mismatch is an issue.
- [ ] Every FR ID declared in an FRD has a cited backlog equivalent, or is an `fr_orphan` issue.
- [ ] No `skip` row dropped silently — each has its reproduced evidence cited in the ledger.
- [ ] No file changed outside `docs/task-tracker-ledger.jsonl`.
- [ ] No branch, PR, or code change created.
