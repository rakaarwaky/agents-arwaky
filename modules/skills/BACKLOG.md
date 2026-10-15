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

| ID | FRD Ref | Work Item | Priority | State | Actual Condition | Owner | Dependencies | Updated |
|----|---------|-----------|:---------|-------|------------------|-------|--------------|---------|
| SKL-01 | FR-SKILLS-001 | List every skill in the pack | P1 | Done | `aa skills list` enumerates the pack sorted by name; 14 unit tests pass at `modules/skills` | @raka | none | 2026-10-15 |
| SKL-02 | FR-SKILLS-002 | Show one skill's guide | P1 | Done | `aa skills show <name>` prints the SKILL.md; matches name / directory / hyphen-free spelling | @raka | none | 2026-10-15 |
| SKL-03 | FR-SKILLS-002 | Ambiguous prefix rejection | P2 | Done | a prefix matching several skills returns not-found rather than guessing | @raka | none | 2026-10-15 |

## Scenario Evidence

- `aa skills list` prints every skill in the pack with its description (verified manually, 2026-10-15).
- `aa skills show fetch` prints the `fetch-mcp` SKILL.md (verified manually, 2026-10-15).
- `aa skills show nope` exits 1 with `Skill not found: nope` (verified manually, 2026-10-15).
- `python3 -m pytest modules/skills/tests -q` → 14 passed (2026-10-15).

## Blockers

- None.

## Dependencies

- The shared kernel (`modules/shared`) provides name sanitisation and
  frontmatter parsing; this feature adds no sibling-feature imports.

## Release Readiness

- Read-only discovery works end to end (`list` and `show`); no provisioning
  behaviour exists by design.

## Deferred

- Nothing planned. Provisioning-like features belong to `modules/harness`.

## Change Log

| Date | Change |
|------|--------|
| 2026-10-15 | created `modules/skills/` (list + show) superseding the removed `modules/skill/` provisioning feature |
