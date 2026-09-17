# BACKLOG.md — The Real-Condition Document

> **Purpose**: Record what is true right now, and on what evidence.
> **Audience**: Engineers, QA, Tech Lead.
> **Boundary**: Specs promise; backlogs report. Two files, never merged.
> **Scope**: One master at the project root. One per feature, beside its spec.

Checked by `aa docs check`:
`status-in-spec` · `spec-without-backlog` · `backlog-without-spec` · `no-master-backlog` ·
`state-vocab-restated` · `undefined-state-vocab` · `master-section-missing` ·
`backlog-section-missing` (the seven sections below, plus the five master-only ones) ·
`unknown-state` · `unknown-state` ·
`done-without-evidence` · `backlog-columns` · `backlog-row-width` · `scenario-without-evidence`.
Invariant definitions → [SKILL.md → Invariants](../SKILL.md#invariants).

A `BACKLOG.md` that restates requirements is a spec. A spec that carries status will rot the moment
code moves. If a backlog row cannot be read without a requirement, the requirement is missing from
the spec — say so in `Actual Condition` and fix the spec.

---

## The Two Kinds

| Kind          | Location                                    | Owns                                                                                         |
|---------------|---------------------------------------------|----------------------------------------------------------------------------------------------|
| Master (root) | Project root — exactly one                  | Feature index, state vocabulary, status policy, roll-up, cross-cutting rows, branches, risk. |
| Per-feature   | Each feature dir, beside its spec — one each| That feature's condition: rows, scenario evidence, release readiness, change log.            |

Five rules keep the pair honest:

1. **Definitions live once.** State vocabulary and status policy belong in the root file
   (`state-vocab-restated`, `undefined-state-vocab`). Feature backlogs cite them; they never repeat them.

2. **Feature backlogs carry file-specific content only.** No policy prose, no state tables,
   no copied paragraphs.

3. **Every feature has both.** A spec row and a backlog row in the root index
   (`spec-without-backlog`, `backlog-without-spec`, `no-master-backlog`).
   A feature with a spec and no backlog is where status leaks into the spec.

4. **ID scopes are explicit.** The root file uses a workspace prefix (`WS-01`).
   Each feature uses its own (`RENDER-01`, `SCRIPT-01`, `DASH-01`).
   A row citing `FR-006` is checked against the spec (`orphan-fr-id`).
   Legacy IDs keep the meaning their owning feature gave them.

5. **Status is verified, not self-reported.** A row reaches `Done` only after someone re-ran
   the evidence command and read its output.

---

## State Vocabulary

### State (rows and headers)

| State         | Meaning                                                        |
|---------------|----------------------------------------------------------------|
| Idea          | Captured, not yet examined; no spec exists for it.             |
| Refinement    | Being specced; a spec or product decision is needed first.     |
| Ready         | Specified enough to start; nobody has started it.              |
| In Progress   | Someone is in it now.                                          |
| Blocked       | Cannot proceed; name the blocker in `Actual Condition`.        |
| In Review     | PR open, awaiting review/CI.                                   |
| QA            | Implemented; awaiting a verification pass against evidence.    |
| Done          | Evidenced complete — cites the command/commit/PR.              |
| Released      | Done and shipped in a release.                                 |
| Deferred      | Intentionally out of current scope; reason in `Actual Condition`. |

### Health (header field on every backlog)

| Health            | Meaning                                                |
|-------------------|--------------------------------------------------------|
| On Track          | Nothing threatens the tier's scope.                    |
| At Risk           | Open gaps could compromise the tier's gate.            |
| Blocked           | Work cannot proceed; name the blocker.                 |
| Ready for QA      | No open backlog items; a verification sweep is outstanding. |
| Ready for Release | All evidence for the feature is recorded.              |
| Released          | Shipped.                                               |

`Done` vs `Released` is a real distinction: a merged fix with no release tag is `Done`.

---

## Status Policy

The root file owns this text. Feature backlogs do not repeat it.

- Status is **verified, not self-reported**. A row reaches `Done` only after someone re-ran the
  evidence command and read its output. `Ready` means "specified, not started", not "broken".
- A recorded verification names a **commit hash**, not "today".
- A PR that merges a fix updates **every** backlog row that fix invalidates, in the same PR.
- `Last Updated` / `Updated` move only with a change in the file.

---

## Writing `Actual Condition`

`aa docs check` enforces the shape of this column (`done-without-evidence`): a `Done` or `Released`
row must contain a backtick code span naming a command and a commit hash. The checker cannot judge
whether the sentence is honest — that part is yours.

### Weak — no command, no number, no commit, nothing to re-run

```
| RENDER-02 | § Test Scenarios | Determinism untested | P0 | Done | Works now | @raka | None | 2026-09-15 |
```

### Strong — names the gate, the result, the commit, and the limit of the claim

```
| RENDER-02 | § Test Scenarios | Determinism scenario has no run-twice-and-compare test | P0 | Done | `tests/integration_renderer_determinism.py::test_rendering_one_fixture_twice_produces_identical_mp4` renders one fixture twice into separate run folders and compares SHA-256; gated on `PSD_RASTER_BACKEND=cpu` (`fa19c37`). | @raka | RENDER-01 | 2026-09-15 |
```

### The honesty rule

Say what is *not* covered as plainly as what is.

> "3 skipped — the GPU-path regressions, which the nightly job runs on llvmpipe and fails on skip"

is the difference between a green row and a green lie.

An open claim the file cannot support belongs in `Next Action`.

---

## Template — Per-Feature `BACKLOG.md`

Copy, fill, delete nothing.

```markdown
# Feature Backlog: <Feature Name>

FRD: [<spec file>](<spec file>)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
AES rules: [RULES_AES.md](../../.agents/rules/RULES_AES.md)
State: <cite root State vocabulary — do not repeat definitions here>
Health: <cite root Health vocabulary — do not repeat definitions here>
Last Updated: <YYYY-MM-DD>

## Current Condition

- Done: <command re-run → counts, at <commit>, on <date>; which files carry each claim>
- In Progress: <None | item>
- Blocked: <None | item and what clears it>
- Next Action: <the one concrete next thing; cite the row ID, and name what this file still cannot assert>

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|---|---|---|---:|---|---|---|---|---|
| <SCOPE>-01 | <FR-001 / § Test Scenarios> | <one work item> | P0 | Ready | <what is true, with the command or commit that shows it> | @<owner> | None | <YYYY-MM-DD> |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|---|---|---|---|---|
| <scenario copied from the spec> | Automated | `tests/<file>` | `test_<name>` | `<commit>` |

Kind values:
- **Automated**: a named test asserts it.
- **Proxy**: a named test asserts a stand-in measurement.
- **Manual**: a human must check it.
- **Gap**: nothing asserts it. An honest record, not a defect.

## Blockers

<None | each blocker and what would clear it>

## Dependencies

<None | rows owned elsewhere that rows here wait on>

## Release Readiness

| Area | Status | Notes |
|---|---|---|
| Tests | Done | `<test command>` → <result> at `<commit>` |
| Type gate | Done | `<the exact command CI runs>` |
| Scenario evidence | Done | <N> of <N> scenarios mapped; which rows are Proxy/Gap and why |
| Docs | Done | [<spec file>](<spec file>) is specification-only; status lives in this file. |

## Deferred

<None | item + reason, recorded so it is not re-litigated every release>

## Change Log

| Date | Change | By |
|---|---|---|
| <YYYY-MM-DD> | <what moved here, with the commit that moved it> | @<owner> |
```

---

## Template — Master Root `BACKLOG.md`

Copy, fill, delete nothing.

```markdown
# BACKLOG — <workspace name>

| Feature | Tier | Spec | Backlog |
|---|---|---|---|
| `modules/<a>` | P0 | [FRD](modules/<a>/FRD.md) | [BACKLOG](modules/<a>/BACKLOG.md) |
| `packages/<b>` | P2 | [PRD](packages/<b>/PRD.md) | [BACKLOG](packages/<b>/BACKLOG.md) |
| `crates/<b>` | P2 | [PRD](crates/<b>/PRD.md) | [BACKLOG](crates/<b>/BACKLOG.md) |

State: <cite State vocabulary definitions below>
Health: <cite Health vocabulary definitions below>
Last Updated: <YYYY-MM-DD>

## Current Condition

- Done: <workspace-level evidence: full test run, lint/type gates, merged PRs>
- In Progress: <None | item>
- Blocked: <None | item>
- Next Action: <the open row IDs that move the workspace forward, cheapest risk-reducer first>

## State Definitions

<State vocabulary table — the single source of truth for all feature backlogs>

<Health vocabulary table — one line per value>

## Status Policy

<The four bullets from the Status Policy section above, plus the ID-prefix table for this workspace>

## Feature Roll-up

| Feature | Tier | State | Health | Next Action |
|---|---|---|---|---|
| `modules/<a>` | P0 | In Progress | On Track | <SCOPE>-01 — <one line> |

## Backlog

Cross-cutting and workspace-level rows only. Anything that belongs to one file goes in that file's backlog.

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|---|---|---|---:|---|---|---|---|---|
| WS-01 | — | <cross-cutting item> | — | Ready | <evidence> | Unassigned | None | <YYYY-MM-DD> |

## Blockers

<None | each blocker>

## Dependencies

<Which rows across features wait on which, and on what decision>

## Release Readiness

Definition of "deployment ready" (target `<version>`):

| Area | Status | Notes |
|---|---|---|
| All P0 done | Done | <gate rows that remain open, by ID> |
| All P1 done + verified | Done | <PR / commit evidence> |
| Tests pass, lint clean, build works | In Progress | <counts at <commit>; which claims are CI jobs vs local habit> |
| Docs complete | Refinement | <which doc defects are open, by row ID> |

## Deferred

<Item + reason for the deferral + the record that keeps it from being re-litigated>

## Change Log

| Date | Change | By |
|---|---|---|
| <YYYY-MM-DD> | <workspace-level change, with PR number and commit> | @<owner> |

## Branches in Flight

| Branch | Backlog IDs | State |
|---|---|---|
| `<prefix>/<name>` | <IDs> | merged as PR #<n> (`<commit>`); worktree pending removal |

## Risk Register

- **Risk:** <what could ship broken>. **Mitigation:** <the row that closes it>.
- **Risk (closed <date>):** <what it was>. **Resolved by** `<commit>`: <evidence>.
```

The last two sections (`Branches in Flight` and `Risk Register`) are root-only, like
`State Definitions` and `Status Policy`: one place that answers "what is in flight" and
"what worries us", so feature files stay about one file.

---

## Verify

```bash
aa docs check . --strict
# Checks: pairing, columns, unknown states, unevidenced Done, scenario coverage.
```
