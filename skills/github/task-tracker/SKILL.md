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
argument-hint: <repo-root> [--dry-run] [--trust | --no-trust] [--legacy] [--scripts-root <dir>]
---

# Task Tracker — zero-trust spec audit → modular GitHub tracking issues with closing conditions

One run covers one repo. It reads the spec-document states, **proves** which rows are
real work and which are fiction, and opens a modular issue per finding. The run outputs
GitHub issues only. It never edits source code, never creates a branch, never opens a
PR. Every issue it opens carries one closing condition: the check whose fulfillment
advances that issue's row to `Done` in its source document.

## Trust modes

The tracker supports two modes for handling `Done` rows:

### `--no-trust` (default)

Zero-trust audit: every `Done` row is treated as a claim that must be proven.
The verifier re-reads the feature's source code and tests to confirm the claimed
behavior is actually implemented and tested. Rows that fail verification become
`unverified` and produce `[DOC-SYNC]` issues demanding proof.

### `--trust`

Trust mode: all `Done` rows are accepted at face value and classified as `skip`
without code verification. Use this when the repo's `Done` markers have been
pre-verified or when the audit is focused on incomplete rows only.
The verifier still processes `Ready`, `In Progress`, and `In Review` rows normally.

Both modes handle the `Next Action` column the same way — see below.

## Next Action handling

Every row carries a `Next Action` (or `Item`) column. The tracker checks this field
for all rows regardless of trust mode:

- **`none` or `<skip>` in Next Action** → the row is classified as `skip_next_action`.
  No issue is created. The ledger records the skip.

- **Next Action has content** (not `none`/`<skip>`) → the verifier checks whether the
  described action is already implemented in the feature's source code and tests:
  - **Action already complete** (code + test exist): verdict `next_action_complete`.
    The tracker opens a `[DOC-SYNC]` issue whose closing condition is the doc edit
    that sets the row's `Next Action` to `none`.
  - **Action not yet complete**: verdict `next_action_pending`.
    The tracker opens a tracking issue whose closing condition is the implementation
    path + test that proves the action, plus the doc edit that sets `Next Action`
    to `done`.

The closing condition for `next_action_pending` issues combines two steps:
1. Implement the described behavior in `<feature>/src/` and add a test in
   `<feature>/tests/` that exercises it; `<test command>` must pass.
2. Set the row's `Next Action` cell to `done` in `<source_doc>`.

## Core invariant (read first)

**Fixing every open issue created by this run must make all tracked FR states = Done.**
This is the contract. If any issue cannot be made to advance its row to `Done` on close,
the run report must flag it as a structural gap (`pending-infra`) so the invariant breach
is visible.

## Zero-trust policy (read first)

No state value in any spec document is trusted. A row marked `Done` is a **claim**,
never a fact. Every row — whatever its state — is verified against live evidence
before it is allowed to be skipped:

- A `Done` row owes proof that the described behavior is actually implemented in the
  feature's current source code (`<feature>/src/`) and exercised by at least one test
  in `<feature>/tests/`.
- A `Done` row owes three proofs, all recorded in the row's `Actual Condition` cell:
  (1) the exact verification command, (2) its pass/fail result, (3) the implementing
  commit SHA. All three must be present and reproduce.
- A `Done` row whose evidence cell carries shipped-release language additionally
  requires release evidence: a public release or deployment that the command
  `gh release view <tag>` confirms (for example `gh release view v6.4.0` reports a
  published release). A tag cited in the doc is a claim, never a fact — the command
  output is the proof.
- An `In Review` row owes proof that a PR exists and is open; the tracker checks
  GitHub for the PR rather than trusting the doc text.
- Evidence that does not reproduce flips the row to `unverified` and produces a
  `[DOC-SYNC]` issue. The doc never gets the benefit of the doubt.

The roll-up gets the same treatment: the ROADMAP `Feature Roll-up` row for a feature is
reconciled against the **actual** state of that feature's backlog rows — a roll-up that
says `Done` while any backlog row is still `In Progress` or `In Review` is a mismatch and
becomes a `[DOC-SYNC]` issue.

When the verifier runs, it never trusts a doc's State Definitions table as
authoritative — it confirms the doc is not a template or scratch file before
relying on the vocabulary it declares.

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
`Ready` while its row table is empty produces a tracking issue for the feature roll-up
row, not for the vanished rows.

If the repo uses neither shape exactly, follow the discovery rule and extract every
table that has both an ID (or Feature) column and a State column.

## State vocabulary

The simplified four-state vocabulary used across the tracked repo:

| State | Meaning |
| --- | --- |
| Ready | Specified; not started. |
| In Progress | Active now. |
| In Review | PR open; awaiting merge/verification. |
| Done | Command + commit evidence recorded in `Actual Condition`. |

Transitions: `Ready` → `In Progress` → `In Review` → `Done`.

The authoritative table for the current repo is its own State Definitions table — parse
it, do not assume the full vocabulary. If the repo still carries legacy state names
(`Idea`, `Refinement`, `Blocked`, `QA`, `Released`, `Deferred`), the scanner records
them verbatim but the classifier maps them to the simplified four: `Idea`/`Refinement`/
`Blocked`/`Deferred` → `Ready` (or `In Progress` when work has started); `QA` →
`In Review`; `Released` → `Done` plus release evidence (a published release that
`gh release view <tag>` confirms; in the tracked repo, `gh release view v6.4.0`).

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
| Ready, In Progress | `incomplete` | tracking issue |
| In Review | `incomplete` | tracking issue, body notes the open PR gate |
| Done whose claimed behavior is confirmed present in the feature's current source code and exercised by at least one test, with command + commit evidence recorded (`--no-trust`) | `skip` | no issue, ledger records the reproduced evidence |
| Done row under `--trust` mode | `skip` | no issue, accepted at face value without code verification |
| Done claim where the described behavior is absent, incomplete, or untested in the feature's source tree | `unverified` | `[DOC-SYNC]` issue demanding proof |
| Any incomplete state where the work is present and tested in the source code but the doc still reports an incomplete state | `doc_sync` | doc-update issue |
| FR ID declared in FRD with no backlog row (or vice versa) | `fr_orphan` | tracking issue on the feature |
| Next Action contains `none` or `<skip>` | `skip_next_action` | no issue, ledger records the skip |
| Next Action has content and the action is already implemented in code + tests | `next_action_complete` | `[DOC-SYNC]` issue: set Next Action to `none` |
| Next Action has content and the action is not yet implemented | `next_action_pending` | tracking issue: implement the action, then set Next Action to `done` |

Legacy state names (`Idea`, `Refinement`, `Blocked`, `QA`, `Released`, `Deferred`) are
recorded verbatim by the scanner and mapped by the classifier to the simplified four
(see the State vocabulary section). There is no path where a `Done` marker alone
suppresses an issue. Doc text is the hypothesis; live evidence is the verdict.

### Evidence rules

| Claim shape | Verification |
| --- | --- |
| behavior described in row | locate the implementing file under `<feature>/src/`; confirm the described function/flag/class/config exists and its logic matches the claim |
| test coverage claimed | locate the test in `<feature>/tests/`; confirm it exercises the described behavior and is not a trivial or disabled test |
| commit hash in row | hash is NOT proof; ignore it and verify the code directly |
| merged PR number in row | PR number is NOT proof; verify the code directly |
| release tag in row | tag is NOT proof; run `gh release view <tag>` and use its output as the proof |

The verifier reads source files, not git history. A hash, PR number, or tag cited in a row is context, not evidence.

### Roll-up double-check

For every `Feature Roll-up` row (roadmap-owned shape) or feature index row
(backlog-owned shape), the verifier recomputes the feature's **effective state** from
its backlog rows:

1. Collect every backlog row of the feature plus its doc-level `State:` line.
2. Effective state = the worst state present, ranked:
   `In Progress` > `In Review` > `Ready` > `Done`.
   Any non-`Done` row makes the feature non-`Done`.
3. If the roll-up row's `State` claims `Done` while the effective state is anything
   less, open `[DOC-SYNC]` on the roll-up row with the offending backlog row ids
   and states listed in the body.
4. If the roll-up claims `Done` and the effective state is `Done`, still re-verify each
   contributing backlog row's evidence per the Evidence rules table — a roll-up is only
   as good as the rows it aggregates.
5. Symmetric check: a feature whose roll-up says `In Progress` or `In Review` while every
   backlog row is verified `Done` with reproducing evidence is also a mismatch
   (under-claimed), and becomes a `[DOC-SYNC]` issue.

The same reconciliation runs on the doc-level `State:` line of a backlog-owned feature
backlog.

## Closing contract

Every issue a run creates carries exactly one `## Closing condition` section. A tracking
issue that names no path to `Done`, or whose path cannot be checked from the body alone,
is incomplete on creation, and the run does not count it until the section is present.

The section holds three fields:

1. **Check** — one observable predicate: the file paths, the behavior that must exist
   there, and the test command that must pass. One issue, one check; a split issue
   carries its own check for its own deliverable.
2. **Advance** — when the check passes, row `<ROW-ID>` sets `State` to `Done` in
   `<source_doc>`, and its evidence cell is rewritten to the commit SHA plus the
   command output that reproduced the check. Every FR ID the row cites advances with
   it: an FR is evidenced only by its backlog rows, so this row's `Done` is that FR's
   `Done` — closing all open issues therefore lands every FR state at `Done`.
3. **Proof** — the commit link and command output posted as the closing comment.

The check's content follows the verdict that produced the issue:

| Verdict producing the issue | Check | Advance |
| --- | --- | --- |
| `open` | the described behavior exists in `<feature>/src/` and one test in `<feature>/tests/` exercises it; `<test command>` passes | row → `Done` |
| `doc_sync` | the doc edit lands: `State` corrected to the reproduced reality, evidence cell citing the verified file and test | row → `Done` |
| `unverified` | the check that failed verification now passes — implementation present in source, one test exercising it | row → `Done` |
| `rollup_mismatch` | every backlog row named in the body independently verifies `Done`, so the roll-up claim becomes true; on an under-claimed roll-up the contributing rows are already `Done` | roll-up row → `Done` |
| `fr_orphan` | a backlog row citing `<FR-ID>` exists and carries reproduced evidence | that row → `Done` |
| `next_action_complete` | the row's `Next Action` cell in `<source_doc>` is set to `none` (the action it described is already verified in code + tests) | row's `Next Action` → `none` |
| `next_action_pending` | the described behavior is implemented in `<feature>/src/` and one test in `<feature>/tests/` exercises it; `<test command>` passes; then the row's `Next Action` cell in `<source_doc>` is set to `done` | row's `Next Action` → `done` |

Rules:

- The check is re-runnable from the issue body alone: exact paths, the behavior, and
  the exact command all appear in the body.
- No proof, no close. Closing without the commit link and command output advances no
  row, and the next run's zero-trust pass returns the row to `unverified`.
- A `[DOC-SYNC]` issue's check is itself the document edit; that edit performs the
  advance the moment it lands.
- If verification disproves a roll-up claim outright, the closing edit corrects the
  roll-up to the effective state instead, and the ledger records that correction as
  the resolution — a `Done` marker is never written for work that does not reproduce.
- A `skip` verdict creates no issue, so it carries no condition; its reproduced
  evidence lives in the ledger.

## Workflow

Run the full `Step 1 → Step 6` pipeline; details live in
[`references/workflow.md`](references/workflow.md).

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
