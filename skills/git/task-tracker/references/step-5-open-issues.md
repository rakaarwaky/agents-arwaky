# Step 5 — open modular issues

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
