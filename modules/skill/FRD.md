# FRD — skill

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.

## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.

## System Overview

The skill feature provisions the agent-skill pack: `agent_skill_orchestrator.py`
implements `ISkillAggregate` (`list_skills`, `check_skills`, `install_skills`,
`uninstall_skills`, `show_skill`, `sync_skills`) over two capabilities —
`capabilities_skill_registry.py` (list/show) and `capabilities_skill_pack.py`
(install/prune/sync + audit, via `utility_skill_pack.py`) — plus
`utility_skill_names.py` for name resolution. The pack lives at
`skills/<category>/<skill>/SKILL.md`; every skill sits in a semantic category
folder, and the harness scans one level below a registered skills root.

Flow: `aa skill <verb>` → `SkillOrchestrator` → registry/pack capability →
skill files under a project's `.agents/skills/` (provisioned) or the pack
itself.

## Functional Requirements

### FR-001: Provision skills into a project

- **Description**: `install_skills(args)` copies pack skills into a target dir,
  writing `.arwaky-skill.json` provenance on each copy.
- **Input**: args (tool/skill/all + `--target`).
- **Output**: `int` exit code; provisioned copies on disk.
- **Business Rules**: only pack-provided skills are copied; a copy carries
  provenance so later `--prune` can remove exactly the provisioned set.
  Hand-written skills in the target are never touched.
- **Edge Cases**: `--prune` deletes only entries carrying provenance (or
  symlinks into `skills/`); a target that already has a copy is refreshed, not
  duplicated.
- **Error Handling**: a pack skill that fails to copy is reported; the rest
  proceed, exit non-zero on any failure.

### FR-002: Audit the skill pack's loadability

- **Description**: `check_skills()` reports layout, name-parity, description,
  uniqueness, and description-budget findings across the pack.
- **Input**: none (reads `skills/`).
- **Output**: `int` exit code; findings by file.
- **Business Rules**: every skill is exactly `skills/<category>/<skill>/SKILL.md`;
  frontmatter `name:` equals the folder; no two skills share a `name:`; the
  aggregate description byte-size stays under budget. An empty category folder
  or a skill dir missing `SKILL.md` is a finding.
- **Edge Cases**: a new category → loads after one harness session restart
  (documented, not an error); a description over budget → finding pointing at
  moving detail into `references/`.
- **Error Handling**: findings are report-only; the audit never rewrites the
  pack.

### FR-003: List and show skills

- **Description**: `list_skills(tool_filter)` enumerates the pack (optionally
  filtered); `show_skill(query)` resolves a name/alias to a skill and renders it.
- **Input**: optional filter / query.
- **Output**: `int` exit code; listing/detail on stdout.
- **Business Rules**: resolution uses `utility_skill_names`; an unknown query is
  a clear miss, not an exception.
- **Edge Cases**: filter matching nothing → empty list, exit 0.
- **Error Handling**: an unresolvable `show` query → "not found" message,
  non-zero.

## API Contract

| Operation | Input | Output | Error Shape | impl / intended |
| `ISkillAggregate.list_skills` | `tool_filter` | `int` + listing | — | impl |
| `ISkillAggregate.check_skills` | — | `int` + findings | non-zero on error findings | impl |
| `ISkillAggregate.install_skills` | `list[str]` | `int` | non-zero on copy failure | impl |
| `ISkillAggregate.uninstall_skills` | `list[str]` | `int` | non-zero | impl |
| `ISkillAggregate.show_skill` | `query` | `int` | non-zero on miss | impl |
| `ISkillAggregate.sync_skills` | `list[str]` | `int` | non-zero | impl |

## Integration Points

| System | Direction | Purpose | Failure mode |
| `skills/` pack | in | the source of provisioned skills | malformed pack → audit finding |
| a project's `.agents/skills/` | out | provisioned copies + provenance | unwritable target → reported |
| harness skill roots | out | registered roots a harness scans | a new category needs one session restart |
| `modules/root_cli_entry.py` (root) | in | `aa skill` | pass-through |

## Non-functional Requirements

| Metric | Target | Measurement method |
| Provisioned-only prune | `--prune` removes only provenance-marked copies | hand-written skills survive a prune |
| Budget | aggregate description bytes under `DESCRIPTION_BUDGET_BYTES` | audit reports the total vs the cap |
| No pack mutation | audit/install never rewrite the pack's `SKILL.md` | pack tree unchanged after an audit |

## Test Scenarios

- `aa skill install` for a named skill into a target copies it with a provenance marker.
- `aa skill check` reports layout/name/description findings across the pack.
- `aa skill install --prune --target .` removes provisioned copies the pack no longer
  provides, leaving hand-written skills in place.

## Assumptions & Constraints

- Provisioning targets a project's `.agents/skills/`, never the pack's own
  `skills/` tree.
- A harness sees a new category only after a session restart; that is a
  documented behavior, not a bug to paper over.

## Glossary

- **pack**: the `skills/<category>/<skill>/SKILL.md` tree under the repo.
- **provenance**: the `.arwaky-skill.json` marker a provisioned copy carries.

