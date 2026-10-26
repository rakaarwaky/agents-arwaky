# Feature Backlog: skills

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-10-26

## Current Condition

- Done: `modules/skills/` vertical slice — contract protocols, contract
  aggregate, taxonomy VOs/entities/errors, the rules SSOT, the shared tree
  and markdown utilities, eight capabilities (index, reader, validator,
  catalog, discoverer, mutator, merge planner, rules renderer), the agent
  orchestrator (including the mutation→catalog pipeline), the root
  container, and the 12-verb CLI surface.
- Done (amended 2026-10-25, PR-5): the feature *reads and authors* the
  pack — the read-only invariant is dropped; the agent dispatches every op
  and owns the mutation→catalog chain.
- Done: `aa skills` exposes every capability of the retired
  skill-authoring CLI — `list`, `show`, `validate`, `catalog`, `discover`,
  `weed`, `repair`, `move`, `archive`, `new-category`, `merge-plan`,
  `rules` — with the legacy exit-code contract (0 / 1 / 2 / 3). Gate:
  `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at
  `767b18672a0c0abd92f7225f267478db8271c334`; Ruff is clean.
- Done: the former `modules/skill/` provisioning feature and the `aa skill`
  command were removed; agents read `skills/` directly and harnesses receive
  the pack through `aa connect`.
- Done: the pack scripts (`skills/skill-authoring/scripts/`), legacy tests,
  and back-compat shims are retired.
- Blocked: none.
- Next Action: none.

## Backlog

| ID | FRD Ref | Priority | State | Dependencies | Next Action | Updated | Actual Condition |
|---|---|---|---|---|---|---|---|
| SKL-01 | FR-SKILLS-001, FR-SKILLS-002 | P1 | Done | none | none | 2026-10-26 | `modules/skills/src/root_skills_container.py`, index builder, and reader are exercised by `modules/skills/tests/unit_skills.py`; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| SKL-02 | FR-SKILLS-001, FR-SKILLS-002 | P1 | Done | none | none | 2026-10-26 | `capabilities_skills_index_builder.py` and `capabilities_skills_pack_reader.py`; list/show unit tests; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| SKL-03 | FR-SKILLS-003, FR-SKILLS-004, FR-SKILLS-005, FR-SKILLS-008 | P2 | Done | none | none | 2026-10-26 | Catalog, discovery, validation, and rules capabilities are exercised by `unit_skills_catalog.py`, `unit_skills_validate.py`, and `unit_skills_rules.py`; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| SKL-04 | FR-SKILLS-003, FR-SKILLS-008 | P0 | Done | none | none | 2026-10-26 | Shared rule SSOT and tree walker live in `modules/shared/src/common/utility_skill_pack.py` and `taxonomy_skills_constant.py`; `./.venv/bin/python -m pytest modules/shared -q` → 116 passed and `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| SKL-05 | FR-SKILLS-003, FR-SKILLS-004, FR-SKILLS-005, FR-SKILLS-008 | P0 | Done | SKL-04 | none | 2026-10-26 | Read capabilities and golden fixtures are in `modules/skills/src/capabilities_skills_validator.py` and `modules/skills/tests/`; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| SKL-06 | FR-SKILLS-006, FR-SKILLS-007 | P0 | Done | SKL-05 | none | 2026-10-26 | `capabilities_skills_mutator.py` and `capabilities_skills_merge_planner.py` enforce dry-run and containment; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| SKL-07 | FR-SKILLS-006 | P0 | Done | SKL-06 | none | 2026-10-26 | `agent_skills_orchestrator.py` owns dispatch and the mutation→catalog pipeline; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| SKL-08 | FR-SKILLS-001, FR-SKILLS-002, FR-SKILLS-003, FR-SKILLS-004, FR-SKILLS-005, FR-SKILLS-006, FR-SKILLS-007, FR-SKILLS-008 | P0 | Done | SKL-07 | none | 2026-10-26 | The 12-verb surface is in `modules/cli/src/surface_skills_command.py`; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| SKL-09 | — | P1 | Done | SKL-08 | none | 2026-10-26 | `.github/workflows/ci.yml` invokes the skills catalog/validation gates; `PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m modules.root_cli_entry skills catalog --check` → Catalog in sync; `PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m modules.root_cli_entry skills validate --summary` → 0 issues / 111 skills / 15 categories; `PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest modules/skills modules/shared -q` → 284 passed at `841ac90d09a6a6dc963a568209ecf1894c9773f8`. The full suite passes 684 and Ruff is clean at `767b18672a0c0abd92f7225f267478db8271c334`. |
| SKL-10 | — | P2 | Done | SKL-09 | none | 2026-10-26 | Pack docs point to `aa skills`; legacy suite/shim retirement is reflected in the tracked tree; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| SKL-11 | — | P1 | Done | SKL-10 | none | 2026-10-26 | The legacy pack scripts directory, suite, and back-compat shim are absent from the tracked tree; `git ls-files 'skills/skill-authoring/scripts/**'` → no paths; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| FR-SKILLS-001 | FR-SKILLS-001 | P1 | Done | SKL-02 | none | 2026-10-26 | `capabilities_skills_index_builder.py::list_skills`; `unit_skills.py::test_list_skills_sorted_with_descriptions`; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| FR-SKILLS-002 | FR-SKILLS-002 | P1 | Done | SKL-02 | none | 2026-10-26 | `capabilities_skills_pack_reader.py::show_skill`; `unit_skills.py::test_show_skill_by_frontmatter_name`; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| FR-SKILLS-003 | FR-SKILLS-003 | P1 | Done | SKL-05 | none | 2026-10-26 | `capabilities_skills_validator.py`; golden fixture validation in `modules/skills/tests/unit_skills_validate.py`; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| FR-SKILLS-004 | FR-SKILLS-004 | P1 | Done | SKL-05 | none | 2026-10-26 | `capabilities_skills_catalog.py` rebuild/check; `unit_skills_catalog.py` verifies clean rebuild and drift detection; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| FR-SKILLS-005 | FR-SKILLS-005 | P1 | Done | SKL-03 | none | 2026-10-26 | Catalog search is implemented in `capabilities_skills_catalog.py`; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| FR-SKILLS-006 | FR-SKILLS-006 | P1 | Done | SKL-06 | none | 2026-10-26 | Dry-run-by-default authoring is implemented in `capabilities_skills_mutator.py`; `unit_skills_surface.py::test_mutating_commands_default_to_dry_run`; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| FR-SKILLS-007 | FR-SKILLS-007 | P1 | Done | SKL-06 | none | 2026-10-26 | Read-only merge planning is implemented in `capabilities_skills_merge_planner.py`; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| FR-SKILLS-008 | FR-SKILLS-008 | P1 | Done | SKL-04 | none | 2026-10-26 | Rules render from the shared SSOT through `capabilities_skills_rules_renderer.py`; `modules/skills/tests/unit_skills_rules.py`; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |

## Scenario Evidence

| Scenario | Kind | Test file | Test name | Last verified |
|----------|------|-----------|-----------|---------------|
| `aa skills list` prints every skill in the pack with its description | Automated | `modules/skills/tests/unit_skills.py` | `test_list_skills_sorted_with_descriptions` | `767b186` |
| `aa skills show fetch` prints the `fetch-mcp` SKILL.md | Automated | `modules/skills/tests/unit_skills.py` | `test_show_skill_by_frontmatter_name`, `test_agent_execute_list_and_show` | `767b186` |
| `aa skills show nope` exits 1 with `Skill not found: nope` | Automated | `modules/skills/tests/unit_skills.py` | `test_agent_execute_show_unknown_is_not_ok` | `767b186` |
| `./.venv/bin/python -m pytest modules/skills -q` → 168 passed | Automated | `modules/skills/tests/` | whole-suite pass | `767b186` |
| 13 golden fixtures each report exactly their target issue | Automated | `modules/skills/tests/unit_skills_validate.py` | `test_golden_fixture_per_issue_type` | 2026-10-24 |
| `catalog --check` exits 0 in sync / 3 on drift | Automated | `modules/skills/tests/unit_skills_catalog.py` | `test_check_is_in_sync_immediately_after_rebuild`, `test_check_detects_stale_content_and_counts_the_diff` | `841ac90` |
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
| Legacy retirement | Done | The pack scripts directory, test suite, and back-compat shims are retired |

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
| 2026-10-24 | Retired the legacy script package and the pack's own pytest suite; the shims and the generated pack artifacts remain | @raka |
| 2026-10-25 | FRD/BACKLOG amended: the feature reads and authors (the read-only invariant dropped with the first write path); the agent dispatches every op and owns the mutation→catalog chain | @raka |
| 2026-10-25 | Retired the skill-authoring pack scripts directory (`scripts/cli.py`) and legacy back-compat shims | @raka |
| 2026-10-26 | Added evidence cells for SKL-01 through SKL-11 and explicit FR-SKILLS-001 through FR-SKILLS-008 rows; 168 skills tests pass at `767b186`. | @raka |
| 2026-10-26 | Regenerated `skills/CATALOG.md` from the checked-out pack including its AES skill category; catalog check is in sync, validation reports 0 issues across 111 skills/15 categories, and the skills/shared suites pass 284 tests at `841ac90`. | @raka |
