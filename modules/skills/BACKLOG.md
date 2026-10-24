# Feature Backlog: skills

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-10-24

## Current Condition

- Done: `modules/skills/` vertical slice — contract protocols, contract
  aggregate, taxonomy VOs/entities/errors, the rules SSOT, the shared tree
  and markdown utilities, eight capabilities (index, reader, validator,
  catalog, discoverer, mutator, merge planner, rules renderer), the agent
  orchestrator (including the mutation→catalog pipeline), the root
  container, and the 12-verb CLI surface.
- Done: `aa skills` exposes every capability of the legacy
  `skills/skill-authoring/scripts/cli.py` — `list`, `show`, `validate`,
  `catalog`, `discover`, `weed`, `repair`, `move`, `archive`,
  `new-category`, `merge-plan`, `rules` — with the legacy exit-code
  contract (0 / 1 / 2 / 3). Gate: `python3 -m pytest modules/skills -q`
  → 133 passed; `python3 -m ruff check modules/skills` → clean.
- Done: the former `modules/skill/` provisioning feature and the `aa skill`
  command were removed; agents read `skills/` directly and harnesses receive
  the pack through `aa connect`.
- Done: the legacy script is a delegating shim; the pack's own Python test
  suite and the shim are retired once the shim has shipped for a release.
- Blocked: none.
- Next Action: none.

## Backlog

| ID | Priority | State | Dependencies | Next Action | Updated |
|---|---|---|---|---|---|
| SKL-01 | P1 | Done | none | none | 2026-10-15 |
| SKL-02 | P1 | Done | none | none | 2026-10-15 |
| SKL-03 | P2 | Done | none | none | 2026-10-15 |
| SKL-04 | P0 | Done | none | none — rules SSOT + walker lifted into `modules/shared` | 2026-10-24 |
| SKL-05 | P0 | Done | SKL-04 | none — read capabilities (validate/catalog/discover/rules) ported with golden fixtures | 2026-10-24 |
| SKL-06 | P0 | Done | SKL-05 | none — mutating capabilities + merge planner ported; dry-run and containment pinned | 2026-10-24 |
| SKL-07 | P0 | Done | SKL-06 | none — agent dispatch + mutation→catalog pipeline owned by the agent | 2026-10-24 |
| SKL-08 | P0 | Done | SKL-07 | none — 12-verb `aa skills` surface; legacy output parity pinned | 2026-10-24 |
| SKL-09 | P1 | Done | SKL-08 | none — CI flips to the new commands; pack scripts reduced to a shim | 2026-10-24 |
| SKL-10 | P2 | Done | SKL-09 | none — pack docs point at `aa skills`; legacy suite + shim retired | 2026-10-24 |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa skills list` prints every skill in the pack with its description | Manual | — | verified manually | 2026-10-15 |
| `aa skills show fetch` prints the `fetch-mcp` SKILL.md | Manual | — | verified manually | 2026-10-15 |
| `aa skills show nope` exits 1 with `Skill not found: nope` | Manual | — | verified manually | 2026-10-15 |
| `python3 -m pytest modules/skills/tests -q` → 133 passed | Automated | `modules/skills/tests/` | whole-suite pass | 2026-10-24 |
| 13 golden fixtures each report exactly their target issue | Automated | `modules/skills/tests/unit_skills_validate.py` | `test_golden_fixture_per_issue_type` | 2026-10-24 |
| `catalog --check` exits 0 in sync / 3 on drift | Automated | `modules/skills/tests/unit_skills_catalog.py` | `test_check_is_in_sync_immediately_after_rebuild`, `test_check_detects_stale_content_and_counts_the_diff` | 2026-10-24 |
| Every mutating verb is dry-run by default | Automated | `modules/skills/tests/unit_skills_surface.py` | `test_mutating_commands_default_to_dry_run` | 2026-10-24 |
| `move --apply` applies once then rebuilds once | Automated | `modules/skills/tests/integration_skills.py` | `test_move_apply_applies_once_then_rebuilds_once` | 2026-10-24 |
| Symlinked destinations fail closed at plan and apply | Automated | `modules/skills/tests/unit_skills_mutate.py` | `test_symlinked_target_category_cannot_escape_the_root`, `test_symlink_created_after_plan_fails_at_apply` | 2026-10-24 |

## Blockers

- None.

## Dependencies

- The shared kernel (`modules/shared`) provides name sanitisation and
  frontmatter parsing; this feature adds no sibling-feature imports.

## Release Readiness

| Area | Status | Notes |
|------|--------|-------|
| Discovery | Done | `list` and `show` work end to end; the surface is byte-stable |
| Authoring | Done | `validate`, `catalog`, `discover`, `weed`, `repair`, `move`, `archive`, `new-category`, `merge-plan`, `rules` all dispatch through the aggregate |
| CI | Done | `validate --summary` + `catalog --check` run the new code; `pytest modules/` and `lac scan modules/` are blocking steps |
| Legacy retirement | Done | The script is a one-release shim; the pack suite is retired with it |

## Deferred

- Unifying the two pack walkers (`utility_skill_pack.py` for read discovery,
  `utility_skills_tree.py` for authoring) — the cross-check test pins their
  agreement; the unification is a follow-up refactor.
- Symlinked skill *folders*: recursive scans deliberately do not descend
  symlinks (a loop cannot hang a scan). Revisit only if such folders are
  wanted.
- Executing a merge: `merge-plan` stays read-only; `skill-lifecycle`
  executes merges agent-side.

## Change Log

| Date | Change | By |
|------|--------|----|
| 2026-10-15 | created `modules/skills/` (list + show) superseding the removed `modules/skill/` provisioning feature | @raka |
| 2026-10-23 | Scenario Evidence, Release Readiness, and Change Log converted to the AES606 template tables | @raka |
| 2026-10-24 | Feature amended from read-only discovery to read + authoring: the skill-authoring toolchain moved into `modules/skills` and is exposed as 12 `aa skills` verbs; legacy script reduced to a shim | @raka |
