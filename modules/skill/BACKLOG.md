# Feature Backlog: skill

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-09-18

## Current Condition

- Done: `SkillOrchestrator` + 2 capabilities + `ISkillAggregate`/`ISkillProvisioner` contracts + pack utilities at `5556fd5`; `aa check` reports 99 skills across 20 categories, names unique, layout loadable at `5556fd5`.
- In Progress: skill-03 — FRD/BACKLOG pair authoring (this file).
- Blocked: none.
- Next Action: close this pair; then SKL-01 sweep (provision + prune into a scratch target).

## Backlog

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| SKL-01 | FR-SKILL-001 | Provision + prune skills with provenance | P1 | QA | install/prune capabilities present at `5556fd5`; `aa check` loadability green at `5556fd5`. Scratch-target round-trip outstanding. | @raka | None | 2026-09-18 |
| SKL-02 | FR-SKILL-002 | Pack loadability audit (layout/name/description) | P1 | Done | `aa check` skill-pack gate at `5556fd5` → 99 skills, names unique, layout loadable. | @raka | None | 2026-09-18 |
| SKL-03 | FR-SKILL-001–FR-SKILL-003 | FRD + BACKLOG pair authoring for skill | P1 | In Progress | Files written in this sweep. | @raka | None | 2026-09-18 |

## Scenario Evidence (rows)

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa skill install <skill> --target .` copies the skill with a provenance marker. | Proxy | manual | `aa skill install …` then inspect `.arwaky-skill.json` | `5556fd5` |
| `aa skill check` reports layout/name/description findings across the pack. | Proxy | manual | `aa check` skill gate → 99 skills at `5556fd5` | `5556fd5` |
| `aa skill install --prune --target .` removes provisioned copies the pack no longer provides. | Gap | — | — | `5556fd5` (no automated test yet) |

## Blockers

None.

## Dependencies

None.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Tests | QA | import + `aa check` at `{C}`; prune round-trip outstanding |
| Type gate | Done | `aa check` at `{C}` |
| Docs | In Progress | SKL-03 (this pair) |

## Deferred

None.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-09-18 | FRD/BACKLOG pair created during WS-04 doc sweep at `5556fd5`. | @raka |
