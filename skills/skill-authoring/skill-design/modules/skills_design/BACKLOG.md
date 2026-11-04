# BACKLOG — skills_design

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../../../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-04

## Progress Overview

- Done: `skills/skill-authoring/skill-design/modules/skills_design/` vertical slice — contract protocols, contract
  aggregate, taxonomy VOs/entities/errors, the rules SSOT, the shared tree
  and markdown utilities, design-side capabilities (lister, reader, linter,
  catalog, discoverer, mover, archiver, creator), the agent
  orchestrator (including the mutation→catalog pipeline), the root
  container, and the 8 design-side CLI verbs (list, read, lint, catalog,
  discover, move, archive, create). The trace pipeline lives in
  `skills/skill-authoring/skill-traces/modules/skills_traces/` and is wired into the same aggregate via the
  shared contract layer.
- Done (amended 2026-10-25, PR-5): the feature *reads and authors* the
  pack — the read-only invariant is dropped; the agent dispatches every op
  and owns the mutation→catalog chain.
- Done: `aa skills` exposes every capability of the retired
  skill-authoring CLI — `list`, `show`, `validate`, `catalog`, `discover`,
  `weed`, `repair`, `move`, `archive`, `new-category` — with the legacy exit-code contract (0 / 1 / 2 / 3). Gate:
  `uv run pytest skills/skill-authoring/skill-design/modules/skills_design -q` → 125 passed at
  `37b76d738e6767869fc2ee8c2008a160177b1fa1`; Ruff is clean.
- Done: the former `modules/skill/` provisioning feature and the `aa skill`
  command were removed; agents read `skills/` directly and harnesses receive
  the pack through `aa connect`.
- Done: the pack scripts (`skills/skill-authoring/scripts/`), legacy tests,
  and back-compat shims are retired.
- Blocked: none.
- Next Action: none.

Note: the SKL-NN implementation-tracking entries were removed and their
evidence folded into the FR-SkillsDesign-NNN Backlog Status entries below,
because the linter ID-matching rule only allows BACKLOG entry IDs that
the paired spec (FRD) declares — the SKL-NN IDs have no spec-declared
counterpart.

## Backlog Status

### FR-SkillsDesign-001: List Skills

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_skills_lister.py::list_skills` and the lister/reader in `root_skills_container.py` are exercised by `unit_skills.py::test_list_skills_sorted_with_descriptions`; `uv run pytest skills/skill-authoring/skill-design/modules/skills_design -q` → 125 passed at `37b76d738e6767869fc2ee8c2008a160177b1fa1`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-SkillsDesign-002: Show Skill Guide

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_skills_reader.py::show_skill`; `unit_skills.py::test_show_skill_by_frontmatter_name`; `uv run pytest skills/skill-authoring/skill-design/modules/skills_design -q` → 125 passed at `37b76d738e6767869fc2ee8c2008a160177b1fa1`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-SkillsDesign-003: Validate Pack

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | The 13-rule validator checks live inline in `capabilities_skills_linter.py::SkillsLinter` (folded from the retired `capabilities_skills_validator.py`); the shared rule SSOT lives in `modules/shared/src/common/utility_skill_pack.py` and `taxonomy_skills_constant.py`; golden fixtures in `unit_skills_validate.py::test_golden_fixture_per_issue_type`; `uv run pytest skills/skill-authoring/skill-design/modules/skills_design -q` → 125 passed at `37b76d738e6767869fc2ee8c2008a160177b1fa1`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-SkillsDesign-004: Rebuild Catalog

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_skills_catalog.py` rebuild/check; `unit_skills_catalog.py` verifies clean rebuild and drift detection; `uv run pytest skills/skill-authoring/skill-design/modules/skills_design -q` → 125 passed at `37b76d738e6767869fc2ee8c2008a160177b1fa1`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-SkillsDesign-005: Search Catalog

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | Catalog search is implemented in `capabilities_skills_catalog.py`; `uv run pytest skills/skill-authoring/skill-design/modules/skills_design -q` → 125 passed at `37b76d738e6767869fc2ee8c2008a160177b1fa1`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-SkillsDesign-006: Author Pack

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `utility_skills_mutation.py` enforces dry-run and containment; `agent_skills_orchestrator.py` owns the mutation→catalog pipeline; `unit_skills_mutate.py::test_mutating_commands_default_to_dry_run` and `integration_skills.py::test_move_apply_applies_once_then_rebuilds_once`; `uv run pytest skills/skill-authoring/skill-design/modules/skills_design -q` → 125 passed at `37b76d738e6767869fc2ee8c2008a160177b1fa1`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-10-26                                                   |

### FR-SkillsDesign-007: Plan Merge

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Removed                                                        |
| Done         | Removed — the read-only merge planner (`capabilities_skills_merge_planner.py`, `ISkillsMergePlannerProtocol`, `MergePlan` VO, and the `aa skills merge-plan` verb) was deep-cleaned out; `skill-lifecycle` owns merge execution agent-side. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-03                                                   |

### FR-SkillsDesign-008: Create Skill or Category

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `capabilities_skills_creator.py::create_skill` / `create_category`; `unit_skills.py` covers name/category validation, dry-run, and `--apply`; `uv run pytest skills/skill-authoring/skill-design/modules/skills_design -q` → 125 passed at `37b76d738e6767869fc2ee8c2008a160177b1fa1`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-03                                                   |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | <Business goals, user stories, and scope>       | [PRD.md](../../../../../PRD.md) |
| FRD          | <Functional requirements specification>         | [FRD.md](FRD.md) |
| ROADMAP      | <Timeline, phasing, and dependencies>           | [ROADMAP.md](../../../../../ROADMAP.md) |
| ARCHITECTURE | <System boundaries, tech stack, and infra>      | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |
