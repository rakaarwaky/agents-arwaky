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

| Feature | Tier | Spec | Backlog |
|---|---|---|---|
| modules/<a> | P0 | [FRD](modules/<a>/FRD.md) | [BACKLOG](modules/<a>/BACKLOG.md) |

State: cite State vocabulary definitions below
Health: cite Health vocabulary definitions below
Last Updated: <YYYY-MM-DD>

## Current Condition

- Done: <workspace-level evidence>
- In Progress: <None | item>
- Blocked: <None | item>
- Next Action: <the open row IDs that move the workspace forward>

## State Definitions

| State | Meaning |
|---|---|
| Idea | Captured, not yet examined; no spec exists for it. |
| Refinement | Being specced; a spec or product decision is needed first. |
| Ready | Specified enough to start; nobody has started it. |
| In Progress | Someone is in it now. |
| Blocked | Cannot proceed; name the blocker in Actual Condition. |
| In Review | PR open, awaiting review/CI. |
| QA | Implemented; awaiting a verification pass against evidence. |
| Done | Evidenced complete — cites the command/commit/PR. |
| Released | Done and shipped in a release. |
| Deferred | Intentionally out of current scope; reason in Actual Condition. |

| Health | Meaning |
|---|---|
| On Track | Nothing threatens the tier's scope. |
| At Risk | Open gaps could compromise the tier's gate. |
| Blocked | Work cannot proceed; name the blocker. |
| Ready for QA | No open backlog items; a verification sweep is outstanding. |
| Ready for Release | All evidence for the feature is recorded. |
| Released | Shipped. |

## Status Policy

- Status is verified, not self-reported.
- A row reaches Done only after someone re-ran the evidence command and
  read its output.
- A recorded verification names a commit hash, not "today".
- A PR that merges a fix updates every backlog row that fix invalidates,
  in the same PR.

| Scope | Prefix | Example |
|---|---|---|
| Workspace / cross-cutting | WS- | WS-01 |
| Feature <a> | <SCOPE_A>- | <SCOPE_A>-01 |

## Feature Roll-up

| Feature | Tier | State | Health | Next Action |
|---|---|---|---|---|
| modules/<a> | P0 | In Progress | On Track | <SCOPE>-01 — <one line> |

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|---|---|---|---:|---|---|---|---|---|
| WS-01 | — | <cross-cutting item> | — | Ready | <evidence> | Unassigned | None | <YYYY-MM-DD> |

## Blockers

<None | each blocker>

## Dependencies

<Which rows across features wait on which, and on what decision>

## Release Readiness

| Area | Status | Notes |
|---|---|---|
| All P0 done | Done | <gate rows that remain open, by ID> |
| Tests pass, lint clean | In Progress | <counts at <commit>> |

## Deferred

<Item + reason for the deferral>

## Change Log

| Date | Change | By |
|---|---|---|
| <YYYY-MM-DD> | <workspace-level change, with PR number and commit> | @<owner> |

## Branches in Flight

| Branch | Backlog IDs | State |
|---|---|---|
| <prefix>/<name> | <IDs> | merged as PR #<n> (<commit>) |

## Risk Register

- Risk: <what could ship broken>. Mitigation: <the row that closes it>.
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
