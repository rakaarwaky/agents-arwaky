---
name: skill-design
description: Authors, repairs, audits, and prunes agent skills. --create builds a new SKILL.md from a described job; --improve repairs an existing one; --audit checks and fixes skills to the shared lint standard (structure, naming, frontmatter, dangling refs, reference-pattern); --prune reads every skill's description and body, then merges skills that duplicate, share a bounded purpose, or share tooling into one consolidated folder, archiving the dropped duplicates. Use when creating, improving, auditing, or consolidating skills.
user-invocable: true
when-to-use: Author a new SKILL.md for a slash command that has no loaded skill, or improve an existing SKILL.md without losing intent.
argument-hint: "<skills path> [--create | --improve | --audit | --prune] [--dry-run | --headless]"
---

# Skill Design

You author, repair, audit, and prune agent skill directories (a collection of `SKILL.md` folders). Four modes own four distinct jobs; pick one per invocation.

**Purpose of this skill:** keep the skill tree holding skills that read clean, invoke correctly, follow the shared body shape and lint standard, and carry no duplicate or overlapping folders. `--create` builds from a described job; `--improve` repairs an existing skill in place; `--audit` makes a target conform to the lint standard; `--prune` collapses duplicate or same-purpose skills into one folder.

## Global Rules

Rules that apply to every step. Reference files cite these; they never restate them.

- **Mode scope**: `--create` and `--improve` author/repair a single skill; `--audit` works on a single skill or a pack and makes it conform to the lint standard; `--prune` works on a category or the whole tree and collapses overlap. Each mode routes to its own reference; they do not share state.
- **One home per fact.** Each rule, value, or list lives in a single authoritative place — a Global Rules bullet below or a reference file. When an edit touches an existing copy elsewhere, make the requested change and report the duplication instead of silently rewriting.
- **No no-op sentences.** If a sentence does not change behavior — "be careful", "use best practices", a guardrail restating the instruction it follows — delete it or replace it with a checkable criterion.
- **Solve the class, not the instance.** Fix bad output where the fact is owned, not with a downstream check that catches one symptom. Check every generalization against at least two concrete instances.
- **Set degrees of freedom.** High (text steps) for context-dependent work; medium (parameterized scripts) when a preferred pattern exists; low (exact commands) for fragile, strict-sequence operations.
- **Budget for permanent cost.** `description:` and `when-to-use:` are injected into the skill list every session; the body loads per use; `references/*.md` cost nothing until opened. Keep the two trigger fields non-overlapping, and move anything task-conditional out of the body.
- **Consistent terminology.** One term per concept, no synonyms; model-agnostic wording.
- **Dangling refs rot fast.** `related_skills:`, sibling mentions, and cross-skill links are not existence-checked — resolve each against the tree before relying on it, and remove refs to skills that do not exist.
- **Mandatory frontmatter.** Exactly four keys are mandatory: `name`, `description`, `when-to-use`, `argument-hint`; every other key is optional and target-dependent. Full key table: `references/audit/step-2-frontmatter-keys.md`; validator rule catalog: `references/audit/step-3-validator-catalog.md`.
- **Frontmatter semantics.** `description:` = WHAT + WHEN + trigger terms, third person. Trigger phrases the description cannot fit go in `when-to-use:`, never in a `triggers:` key.
- **YAML hygiene.** Quote values containing `: ` or indicator characters (`{ } [ ] * & # ! | > % @`, backtick); never indent a field under a previous field's value (one nested line invalidates the whole frontmatter — only `name`, `description`, `when-to-use` survive recovery); multi-word keys kebab-case (`when_to_use` is the accepted alias).
- **Grok Build parser limits.** `name` ≤ 64 chars; `description` and `when-to-use` ≤ 1,024 chars; top-level `version:`, `triggers:`, and `entry_points:` are ignored.
- **Structure.** Exactly one `SKILL.md` at `<category>/<skill>/SKILL.md` (nested SKILL.md files are rejected). The body is a routing table of contents, ~100–200 lines, with steps that end in checkable completion criteria; detail lives in `references/*.md` (subfolders allowed when the set is large) and every reference, whatever its depth, links directly from `SKILL.md`. Non-trivial logic ships as `scripts/<file>` referenced by path.
- **Mandatory body shape.** Every `SKILL.md` uses exactly three sections: `# Title`, `## Global rules`, `## Routing`. All task data, commands, examples, field shapes, stop conditions, and worked examples belong in `references/*.md` or `scripts/*`. If the body contains anything beyond those three sections, move it to a reference before publishing.
- **Templates are the single source of truth for shape.** `template/template.md` is the entry index; `template/skill.md` is the canonical `SKILL.md` skeleton and `template/reference.md` is the canonical reference-file shape. Every create/improve step copies from the template the index names rather than restating the shape inline; a new artifact kind gets its own `template/<artifact>.md` registered in the index.
- **Audit standard**: `aa skills lint` is the mechanical gate; `references/audit/step-0-overview.md` holds the key table, the validator rule catalog, the reference-pattern decision, and the pre-publish checklist. `--audit` applies that standard to the target and fixes every flagged issue.
- **Prune standard**: two skills covering the same job become one folder with one `SKILL.md`; skills that share a domain but differ per scenario stay one folder with one `SKILL.md` plus a `references/` subfolder, one file per scenario, one level deep. Genuinely different jobs stay separate; note why in the report.
- **Prune phase order**: Phase 1 (remove true duplicates) always precedes Phase 2 (consolidate variants). Merging skills that are already true duplicates is wasted effort.
- **Provisioned copies**: same-folder-name mirrors under `.agents/skills/` or a harness home are provisioned artifacts — keep the repo source, flag the copy for re-provisioning, never edit the copy.
- **Byte-identical or near-identical bodies**: merge into one; keep the more complete body, drop the rest.
- **Same `name:` in two folders**: one is stale; keep the more complete, delete the other.
- **Validation rules** (enforced when auditing, pruning, and consolidating skills): the full rule catalog is `references/audit/step-3-validator-catalog.md`; `aa skills lint` is the mechanical gate.
- **Rollback**: the snapshot (or `HEAD` SHA when the tree was dirty) is the undo path; `git reset --hard <sha>` restores both the skill and unrelated state. Record the snapshot SHA in the commit message and final report. A headless run that cannot commit falls back to `--dry-run` and reports instead of applying.
- **Safety model**: `--dry-run` generates the report and stops before any snapshot or execute. `--headless` generates the same report and continues into the snapshot and execute steps, skipping the interactive approval gate. Read-only steps run immediately in either mode. Destructive actions go to `_archive/` first; permanent delete only with explicit `--hard-delete`.
- **Parallel agents committing in the same tree**: this repo is worked on by multiple agents (GrokBuild via Orca, Hermes). A concurrent commit can sweep your staged changes into someone else's commit and change the HEAD you snapshotted against. After any snapshot and before committing, re-run `git log --oneline -4` and `git status`; re-verify on-disk state before executing; keep your commit scoped to your own task files only — never `git add -A`.
- **Staging discipline**: inside `skills/<category>/`, `git add -A .` stages every tracked file under that subdirectory, not just the change's changes. Use explicit top-level paths (`git add skills/<category>/ skills/CATALOG.md`) and verify the staged set with `git status --short` before committing.

## Routing

| Step        | Reference                                    | Purpose                                                                                                                                                                   |
| ----------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--create`  | [`references/create/`](references/create/)   | produce a publishable `SKILL.md` + `references/` for a job the user describes.                                                                                            |
| `--improve` | [`references/improve/`](references/improve/) | make an existing `SKILL.md` follow the body shape and lint standard without losing the skill's intent.                                                                    |
| `--audit`   | [`references/audit/`](references/audit/)     | make the target skill(s) pass `aa skills lint` and the pre-publish checklist — fix structure, naming, frontmatter, and dangling refs.                                     |
| `--prune`   | [`references/prune/step-0-overview.md`](references/prune/step-0-overview.md) | read every skill's description and body; merge skills that duplicate, share a bounded purpose, or share tooling into one consolidated folder; archive dropped duplicates. |
