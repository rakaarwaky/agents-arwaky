# Task Tracker — scenario references

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

Rows whose source table has a `Next Action` (or `Item`) column: the tracker checks
this field for all of them regardless of trust mode:

- **`none` or `<skip>` in Next Action** → the row is classified as `skip_next_action`.
  No issue is created. The ledger records the skip.
- **Empty Next Action cell** (column present, cell blank) → also `skip_next_action`;
  an empty cell in a table whose shape *has* the column is a "nothing to do" marker.

- **Next Action has content** (not `none`/`<skip>`) → the verifier checks whether the
  described action is already implemented in the feature's source code and tests:
  - **Action already complete** (code + test exist): verdict `next_action_complete`.
    The tracker opens a `[DOC-SYNC]` issue whose closing condition is the doc edit
    that sets the row's `Next Action` to `none`.
  - **Action not yet complete**: verdict `next_action_pending`.
    The tracker opens a tracking issue whose closing condition is the implementation
    path + test that proves the action, plus the doc edit that sets `Next Action`
    to `done`.

Rows whose source table has **no Next Action column at all** (aes-docs Aspect/Detail
entry rows under `## Backlog Status` — the scan emits no `next_action` key for them)
never take the skip path; the `State` row alone classifies them (`Ready` /
`In Progress` / `In Review` → `incomplete`; `Done` → trust-mode `skip` or
`proof_demand`). The distinction is the key's presence, not its content: a missing
column cannot be a "no action" claim.

The closing condition for `next_action_pending` issues combines two steps:
1. Implement the described behavior in `<feature>/src/` and add a test in
   `<feature>/tests/` that exercises it; `<test command>` must pass.
2. Set the row's `Next Action` cell to `done` in `<source_doc>`.

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

## Classification (every row, zero trust)

| Row state | Classification | Action |
| --- | --- | --- |
| Ready, In Progress | `incomplete` | tracking issue |
| In Review | `incomplete` | tracking issue, body notes the open PR gate |
| Done row under `--trust` mode | `skip` | no issue, accepted at face value without code verification |
| Done row under `--no-trust` | `proof_demand` | verifier re-reads source + tests; passes → `skip` (ledger records the reproduced evidence), fails → `unverified` `[DOC-SYNC]` |
| Done claim where the described behavior is absent, incomplete, or untested in the feature's source tree | `unverified` | `[DOC-SYNC]` issue demanding proof |
| Any incomplete state where the work is present and tested in the source code but the doc still reports an incomplete state | `doc_sync` | doc-update issue |
| FR ID declared in FRD with no backlog row (or vice versa) | `fr_orphan` | tracking issue on the feature |
| Next Action column present and cell is empty, `none`, or `<skip>` | `skip_next_action` | no issue, ledger records the skip |
| No Next Action column in the source table (aes-docs entry rows) | state rule above (never `skip_next_action`) | classified by `State` alone |
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

For every `Feature Roll-up` row (roadmap-owned shape), feature index row
(backlog-owned shape), or `## Roadmap Status` PR entry (aes-docs shape, feature
resolved from the entry's `Backlog` link), the verifier recomputes the feature's
**effective state** from its backlog rows. The claim's feature key arrives in
path form (`modules/<name>` from a Roll-up ID cell, `crates/<name>` from a
Backlog link) and is matched to the feature's rows by the path's last segment
(`modules/daemon` → rows grouped under `daemon`); a claim for a feature with no
rows at all is checked against `Done`:

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
