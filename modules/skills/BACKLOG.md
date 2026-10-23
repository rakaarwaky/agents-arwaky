# Feature Backlog: skills

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-10-15

## Current Condition

- Done: `modules/skills/` vertical slice — contract protocol, contract
  aggregate, taxonomy VOs, index builder capability, agent orchestrator,
  root container, and CLI surface — implementing `aa skills list` and
  `aa skills show`. Gate: `python3 -m pytest modules/skills -q` → 14 passed;
  `python3 -m ruff check modules/` → clean;
  `python3 -m mypy modules/skills/` → no errors in `modules/skills`.
- Done: the former `modules/skill/` provisioning feature and the `aa skill`
  command were removed; agents read `skills/` directly and harnesses receive
  the pack through `aa connect`.
- Blocked: none.
- Next Action: none. Add provisioning-like features to `modules/harness`
  (`aa connect`), not here.

## Backlog

| ID | Priority | State | Dependencies | Next Action | Updated |
|---|---|---|---|---|---|
| SKL-01 | P1 | Done | none | none | 2026-10-15 |
| SKL-02 | P1 | Done | none | none | 2026-10-15 |
| SKL-03 | P2 | Done | none | none | 2026-10-15 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa skills list` prints every skill in the pack with its description | Manual | — | verified manually | 2026-10-15 |
| `aa skills show fetch` prints the `fetch-mcp` SKILL.md | Manual | — | verified manually | 2026-10-15 |
| `aa skills show nope` exits 1 with `Skill not found: nope` | Manual | — | verified manually | 2026-10-15 |
| `python3 -m pytest modules/skills/tests -q` → 14 passed | Automated | `modules/skills/tests/` | whole-suite pass | 2026-10-15 |

## Blockers

- None.

## Dependencies

- The shared kernel (`modules/shared`) provides name sanitisation and
  frontmatter parsing; this feature adds no sibling-feature imports.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Discovery | Done | Read-only discovery works end to end (`list` and `show`); no provisioning behaviour exists by design |

## Deferred

- Nothing planned. Provisioning-like features belong to `modules/harness`.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-10-15 | created `modules/skills/` (list + show) superseding the removed `modules/skill/` provisioning feature | @raka |
| 2026-10-23 | Scenario Evidence, Release Readiness, and Change Log converted to the AES606 template tables | @raka |
