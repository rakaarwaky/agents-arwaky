# FRD — skill

> Functional Requirements Document. Describes HOW this feature works functionally.
> Audience: Engineers, QA, Tech Lead.


## Reference

- PRD: [PRD.md](../../PRD.md)
- Backlog: [BACKLOG.md](BACKLOG.md) — real condition for this feature; this file is specification only.


## System Overview

The skill feature provisions the shared agent-skill pack into project
workspaces and reports what the pack contains. One orchestrator exposes
list, check, show, install, uninstall, and sync — the registry side answers
queries, the pack side provisions and audits.

Flow: `aa skill <action>` → skill orchestrator → registry/pack capability →
a project's `.agents/skills/` (provisioned copies) or the pack itself.


## Functional Requirements

### FR-SKILL-001: Provision skills into a project

- **Description**: install copies pack skills into a target workspace,
  writing a provenance marker on each copy.
- **Input**: scope (tool name, skill name, or `all`) and target directory
  (plus optional dest, force, link, prune flags).
- **Output**: exit code; provisioned copies under the target's
  `.agents/skills/`.
- **Business Rules**: only pack-provided skills are copied; a copy carries
  `.arwaky-skill.json` provenance so a later prune can remove exactly the
  provisioned set. Hand-written skills in the target are never touched, and
  the pack's own tree is never written.
- **Edge Cases**: `all` provisions every pack skill; a target that already
  has a copy is skipped or refreshed with force, not duplicated; `--prune`
  alone (no scope) prunes without provisioning.
- **Error Handling**: a pack skill that fails to copy is reported and the
  rest proceed; any failure exits non-zero.

### FR-SKILL-002: Audit the skill pack's loadability

- **Description**: check reports layout, name-parity, description,
  uniqueness, and description-budget findings across the pack, alongside
  per-tool coverage.
- **Input**: none (reads the pack); optional machine-readable flag.
- **Output**: exit code; findings by file (or JSON with the flag).
- **Business Rules**: every skill is exactly one category level deep under
  the pack root; frontmatter name equals the folder; no two skills share a
  name; aggregate description bytes stay under the budget; an empty category
  or a skill dir missing its manifest file is a finding.
- **Edge Cases**: a brand-new category loads only after one harness session
  restart (documented behaviour, not an error); a description over budget is
  a finding pointing at moving detail into per-skill references.
- **Error Handling**: findings are report-only; the audit exits non-zero on
  any finding and never rewrites the pack.

### FR-SKILL-003: Query skills (list / show)

- **Description**: list enumerates the manifest tools and the shared pack
  (optionally filtered to one tool); show resolves a name or alias to a
  skill and renders its manifest file.
- **Input**: optional tool filter (list) / name or alias query (show).
- **Output**: exit code; listing table or skill document on stdout.
- **Business Rules**: the pack is shared — every tool sees the same skills;
  resolution goes through the shared skill-name helpers; an unknown query is
  a clear miss, not an exception.
- **Edge Cases**: a filter matching nothing prints a not-found line and
  exits non-zero; a tool holding several skills shows the primary one and
  lists the rest.
- **Error Handling**: an unresolvable show query prints a not-found message
  and exits non-zero.

### FR-SKILL-004: Install / uninstall through the CLI surface

- **Description**: the surface routes install and uninstall actions —
  including their aliases and per-subcommand help — to the provisioning
  handlers.
- **Input**: scope (tool / skill / `all`), target directory, and flags
  (dest, force, link, copy, prune for install; dest for uninstall).
- **Output**: exit code; per-skill provision/removal lines on stdout.
- **Business Rules**: install provisions copies by default (link only on
  explicit request, because a workspace copy must survive outside this
  checkout); uninstall removes only provisioned or linked entries and never
  the pack source; the default target is the current working directory's
  `.agents/skills/`.
- **Edge Cases**: uninstall of an unknown scope exits non-zero with a
  pointer to list; `all` walks every manifest tool; help for each
  subcommand is reachable via the help flag.
- **Error Handling**: a missing scope prints usage and exits non-zero; a
  failed copy or removal is reported and the run continues, exiting non-zero
  if anything failed.

### FR-SKILL-005: Re-sync the pack

- **Description**: sync re-provisions the full pack for every tool into the
  target workspace (install-all semantics under one command).
- **Input**: target directory (plus the install flags).
- **Output**: exit code; the target's provisioned set matches the pack.
- **Business Rules**: sync is a pure alias of install-all — same handlers,
  same provenance, same rules as FR-SKILL-001; running it twice is
  idempotent apart from refreshing copies.
- **Edge Cases**: an empty pack reports zero provisions and exits 0; an
  unwritable target fails with the path named.
- **Error Handling**: any copy failure exits non-zero; successes already
  written remain in place.


## API Contract

### Protocol API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `execute` | `op`, `skill?`, `target?` | listing / audit / result | non-zero | — | One method covers provision, audit, query, remove, sync |

### Aggregate API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `list` | `target?` | table | unknown filter → non-zero | tool/skill rows | List the pack, optionally scoped to one tool |
| `check` | `target?` | audit findings | any finding → non-zero | findings banner | Audit pack loadability and per-tool coverage |
| `show` | `name` | skill document | miss → non-zero | skill body | Show one skill's manifest file |
| `install` | `scope`, `target` | result lines | copy failure → non-zero | provision lines | Provision pack skills into a project workspace |
| `uninstall` | `target`, `prune?` | result lines | unknown scope → non-zero | removal lines | Remove provisioned copies from a workspace |
| `sync` | `target` | result lines | copy failure → non-zero | provision lines | Re-provision the full pack for every tool |

## Integration Points

| System | Direction | Purpose | Failure mode |
|--------|-----------|---------|--------------|
| the `skills/` pack | in | source tree every provision copies from | malformed pack → audit finding |
| a project's `.agents/skills/` | out | provisioned copies + provenance marker | unwritable target → reported, non-zero |
| root CLI (`aa skill`) | in | routes list / check / show / install / uninstall / sync | pass-through |
| harness skill roots | out | registered roots a harness scans | a new category needs one session restart |

## Non-functional Requirements

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| Provisioned-only prune | prune removes only provenance-marked copies or links into the pack | hand-written skills survive a prune |
| Description budget | aggregate description bytes stay under the pack budget | audit reports the total vs the cap |
| No pack mutation | check/install never rewrite pack manifest files | pack tree unchanged after an audit |

## Test Scenarios

- `aa skill install` for a named skill into a target copies it with a provenance marker.
- Installing the whole pack for a tool or for `all` copies every pack skill into the target workspace.
- `aa skill check` reports layout, name-parity, description, uniqueness, and budget findings across the pack.
- `aa skill install --prune --target .` removes provisioned copies the pack no longer provides, leaving hand-written skills in place.
- `aa skill list` enumerates every manifest tool with the shared pack size and exits 0.
- `aa skill list` filtered to one tool prints that tool's skill rows and exits 0.
- `aa skill show` for a known skill prints its SKILL.md body and exits 0.
- `aa skill show` for an unknown name prints a not-found message and exits non-zero.
- `aa skill uninstall` removes a provisioned skill directory while leaving the pack source intact.
- `aa skill sync` re-provisions the full pack for every tool into the target workspace.


## Assumptions & Constraints

- Provisioning targets a project's `.agents/skills/`, never the pack's own
  `skills/` tree.
- A harness sees a new category only after a session restart; that is a
  documented behaviour, not a bug to paper over.
- Copies are the default delivery into a workspace so the provision survives
  outside this checkout; links stay an explicit local-only opt-in.


## Glossary

- **pack**: the category-per-skill tree under the repo's `skills/` root.
- **provenance**: the `.arwaky-skill.json` marker a provisioned copy carries.
- **scope**: the tool name, skill name, or `all` an action applies to.
- **workspace**: the target project whose `.agents/skills/` receives copies.
