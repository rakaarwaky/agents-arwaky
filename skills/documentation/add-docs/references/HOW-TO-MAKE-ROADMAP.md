# HOW TO MAKE ROADMAP.md

> **Purpose**: Index features, own shared policy, and record
> workspace-level condition.
>
> **Audience**: Tech Lead, PM, Engineers.
>
> **Boundary**: The single source of truth for workspace state,
> cross-cutting risks, and feature tracking.
>
> **Scope**: Exactly one ROADMAP.md at the project root.
>
> **Location**: Project root.
>
> **Length**: 50–500 lines

---

## Rules

Four rules. Each one prevents a specific failure mode.

1. **Single source of truth.** State vocabulary, Health vocabulary, and
 Status Policy live here and nowhere else. Feature backlogs cite them.
2. **Index every feature.** Every feature directory must appear in the
 Feature Index table, linking to its FRD.md and BACKLOG.md
 (`no-master-roadmap`).
3. **Cross-cutting rows only.** The workspace backlog is for items that
 span multiple features or infrastructure.
4. **ID scopes are explicit.** The root file uses a workspace prefix
 (`WS-01`). Feature prefixes are documented in the Status Policy table.

---

## Template

Copy, fill, delete nothing.

```markdown
# ROADMAP — <workspace name>

State / Health: vocabulary below. Last Updated: <YYYY-MM-DD>

## Current Condition

- Done: <evidence> · In Progress: <None | item> · Blocked: <None | item>
- Next: <open row IDs>

## State Definitions

| State | Meaning |
|---|---|
| Idea | Not examined; no spec. |
| Refinement | Being specced. |
| Ready | Specified; not started. |
| In Progress | Active now. |
| Blocked | Name the blocker in Actual Condition. |
| In Review | PR open. |
| QA | Awaiting verification pass. |
| Done | Command + commit evidence. |
| Released | Shipped. |
| Deferred | Out of scope; reason in Actual Condition. |

| Health | Meaning |
|---|---|
| On Track | No threat to tier. |
| At Risk | Gaps may miss the gate. |
| Blocked | Cannot proceed. |
| Ready for QA | Open rows clear; sweep left. |
| Ready for Release | Evidence recorded. |
| Released | Shipped. |

## Status Policy

- Verified, not self-reported: re-run command; cite commit hash (not "today").
- Same PR updates every backlog row the change invalidates.
- Prefixes: workspace `WS-` · feature `<SCOPE>-` (feature rows stay in their BACKLOG).

## Feature Roll-up

Index + state in one table (links = the feature index).

| Feature | Tier | Spec | Backlog | State | Health | Next |
|---|---|---|---|---|---|---|
| modules/<a> | P0 | [FRD](modules/<a>/FRD.md) | [BACKLOG](modules/<a>/BACKLOG.md) | In Progress | On Track | <SCOPE>-01 |

## Backlog

Workspace / cross-cutting rows only.

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|---|---|---|---:|---|---|---|---|---|
| WS-01 | — | <item> | — | Ready | <evidence> | Unassigned | None | <YYYY-MM-DD> |

## Blockers

<None | blocker + what clears it>

## Dependencies

<None | cross-feature wait + decision>

## Release Readiness

| Area | Status | Notes |
|---|---|---|
| P0 / gates | <State> | <IDs or counts at <commit>> |

## Deferred

<None | item + reason>

## Change Log

| Date | Change | By |
|---|---|---|
| <YYYY-MM-DD> | <change + PR/commit> | @<owner> |

## Branches in Flight

| Branch | Backlog IDs | State |
|---|---|---|
| <prefix>/<name> | <IDs> | <state / PR #n> |

## Risk Register

- Risk: <what ships broken>. Mitigation: <row ID>.
```

---

## Section Contract

Every section is required unless marked optional. Each exists for one
reason.

| Section            | Why it belongs here                                          |
| ------------------ | ------------------------------------------------------------ |
| Feature index      | Shows every feature, its spec, and its backlog in one place. |
| Current Condition  | Gives workspace-level truth before detail.                   |
| State Definitions  | Single source of truth for all states and health values.     |
| Status Policy      | Single source of truth for verification and ID prefixes.     |
| Feature Roll-up    | Shows state and health across features.                      |
| Backlog            | Cross-cutting and workspace-level rows only.                 |
| Blockers           | Workspace blockers, not feature-local noise.                 |
| Dependencies       | Cross-feature dependencies and decisions.                    |
| Release Readiness  | Workspace definition of deployment ready.                    |
| Deferred           | Workspace-level deferrals.                                   |
| Change Log         | Workspace-level changes.                                     |
| Branches in Flight | One place to see active branches and their owned rows.       |
| Risk Register      | One place to record what could ship broken.                  |

---

## Verify

```bash
aa docs check . --strict
# Checks: master root presence, feature pairing, unknown states, missing sections.
```
