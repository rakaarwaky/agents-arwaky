# HOW TO MAKE BACKLOG.md

> **Purpose**: Record what is true right now for one feature, and on what
> evidence.
>
> **Audience**: Engineers, QA, Tech Lead.
>
> **Boundary**: Specs promise; backlogs report. Two files, never merged.
>
> **Scope**: One BACKLOG.md per feature folder.
>
> **Location**: Inside the feature's directory
>
> **Length**: 50–500 lines

---

## Rules

Five rules. Each one prevents a specific failure mode.

1. **Definitions live once.** State vocabulary and status policy belong in
 the root file (ROADMAP.md). Feature backlogs cite them; they never repeat
 them (`state-vocab-restated`, `undefined-state-vocab`).
2. **Feature backlogs carry file-specific content only.** No policy prose, no
 state tables, no copied paragraphs from the root.
3. **Every feature has both.** A spec and a backlog must exist beside each
 other (`spec-without-backlog`, `backlog-without-spec`).
4. **ID scopes are explicit.** Each feature uses its own prefix
 (`RENDER-01`, `SCRIPT-01`). A row citing `FR-006` is checked against the
 spec (`orphan-fr-id`).
5. **Status is verified, not self-reported.** A Done or Released row must
 contain a backtick code span naming a command and a commit hash
 (`done-without-evidence`).

---

## Template

Copy, fill, delete nothing.

```markdown
# Feature Backlog: <Feature Name>

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md), if applicable
State: cite root ROADMAP.md state vocabulary. Do not repeat definitions here.
Health: cite root ROADMAP.md health vocabulary. Do not repeat definitions
here.
Last Updated: <YYYY-MM-DD>

## Current Condition

- Done: <command re-run → counts, at <commit>, on <date>>
- In Progress: <None | item>
- Blocked: <None | item and what clears it>
- Next Action: <the one concrete next thing; cite the row ID>

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|---|---|---|---:|---|---|---|---|---|
| <SCOPE>-01 | <FR-001> | <one work item> | P0 | Ready | <what is true, with the command or commit> | @<owner> | None | <YYYY-MM-DD> |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|---|---|---|---|---|
| <scenario copied from the spec> | Automated | tests/<file> | test_<name> | <commit> |

Kind values: Automated, Proxy, Manual, Gap.

## Blockers

<None | each blocker and what would clear it>

## Dependencies

<None | rows owned elsewhere that rows here wait on>

## Release Readiness

| Area | Status | Notes |
|---|---|---|
| Tests | Done | <test command> → <result> at <commit> |
| Scenario evidence | Done | <N> of <N> scenarios mapped |
| Docs | Done | [FRD.md](FRD.md) is specification-only. |

## Deferred

<None | item + reason>

## Change Log

| Date | Change | By |
|---|---|---|
| <YYYY-MM-DD> | <what moved here, with the commit> | @<owner> |
```

---

## Section Contract

Every section is required unless marked optional. Each exists for one
reason.

| Section           | Why it belongs here                                     |
| ----------------- | ------------------------------------------------------- |
| Header links      | Connects the backlog to its FRD and shared root policy. |
| Current Condition | Gives the truth before the table, not after it.         |
| Backlog           | The work rows for this feature only.                    |
| Scenario Evidence | Maps FRD scenarios to real tests or honest gaps.        |
| Blockers          | Names what stops work and what clears it.               |
| Dependencies      | Names rows owned elsewhere that this feature waits on.  |
| Release Readiness | Shows whether the feature can ship, with evidence.      |
| Deferred          | Records intentional non-work so it is not re-litigated. |
| Change Log        | Records when and why the condition changed.             |

---

## Verify

```bash
aa docs check . --strict
# Checks: pairing, columns, unknown states, unevidenced Done, scenario coverage.
```
