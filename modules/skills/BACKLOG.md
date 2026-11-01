# Feature Backlog: skills

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-10-26

## Progress Overview

- Done: `modules/skills/` vertical slice — contract protocols, contract
  aggregate, taxonomy VOs/entities/errors, the rules SSOT, the shared tree
  and markdown utilities, seven capabilities (index, reader, validator,
  catalog, discoverer, mutator, merge planner), the agent
  orchestrator (including the mutation→catalog pipeline), the root
  container, and the 12-verb CLI surface.
- Done (amended 2026-10-25, PR-5): the feature *reads and authors* the
  pack — the read-only invariant is dropped; the agent dispatches every op
  and owns the mutation→catalog chain.
- Done: `aa skills` exposes every capability of the retired
  skill-authoring CLI — `list`, `show`, `validate`, `catalog`, `discover`,
  `weed`, `repair`, `move`, `archive`, `new-category`, `merge-plan` — with the legacy exit-code contract (0 / 1 / 2 / 3). Gate:
  `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at
  `767b18672a0c0abd92f7225f267478db8271c334`; Ruff is clean.
- Done: the former `modules/skill/` provisioning feature and the `aa skill`
  command were removed; agents read `skills/` directly and harnesses receive
  the pack through `aa connect`.
- Done: the pack scripts (`skills/skill-authoring/scripts/`), legacy tests,
  and back-compat shims are retired.
- Blocked: none.
- Next Action: none.

Note: the SKL-NN implementation-tracking entries were removed and their
evidence folded into the FR-SKILLS-NNN Backlog Status entries below,
because the linter ID-matching rule only allows BACKLOG entry IDs that
the paired spec (FRD) declares — the SKL-NN IDs have no spec-declared
counterpart.

## Backlog Status

### FR-SKILLS-001: List every skill in the pack

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_skills_index_builder.py::list_skills` and the index/reader in `root_skills_container.py` are exercised by `unit_skills.py::test_list_skills_sorted_with_descriptions`; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-SKILLS-002: Show one skill's guide

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_skills_pack_reader.py::show_skill`; `unit_skills.py::test_show_skill_by_frontmatter_name`; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-SKILLS-003: Validate the pack against the 13 rules

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_skills_validator.py` plus the shared rule SSOT in `modules/shared/src/common/utility_skill_pack.py` and `taxonomy_skills_constant.py`; golden fixtures in `unit_skills_validate.py::test_golden_fixture_per_issue_type`; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-SKILLS-004: Rebuild and guard CATALOG.md

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_skills_catalog.py` rebuild/check; `unit_skills_catalog.py` verifies clean rebuild and drift detection; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-SKILLS-005: Search the catalog

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | Catalog search is implemented in `capabilities_skills_catalog.py`; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-SKILLS-006: Author the pack (dry-run by default)

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_skills_mutator.py` enforces dry-run and containment; `agent_skills_orchestrator.py` owns the mutation→catalog pipeline; `unit_skills_surface.py::test_mutating_commands_default_to_dry_run` and `integration_skills.py::test_move_apply_applies_once_then_rebuilds_once`; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-SKILLS-007: Plan a merge (read-only)

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | Read-only merge planning is implemented in `capabilities_skills_merge_planner.py`; `./.venv/bin/python -m pytest modules/skills -q` → 168 passed at `767b18672a0c0abd92f7225f267478db8271c334`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | <Business goals, user stories, and scope>       | [PRD.md](../../PRD.md) |
| FRD          | <Functional requirements specification>         | [FRD.md](FRD.md) |
| ROADMAP      | <Timeline, phasing, and dependencies>           | [ROADMAP.md](../../ROADMAP.md) |
| ARCHITECTURE | <System boundaries, tech stack, and infra>      | [ARCHITECTURE.md](../../ARCHITECTURE.md) |
