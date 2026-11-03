---
name: skill-library
description: Audits and prunes the agent skill tree. --audit checks and fixes skills to the shared lint standard (structure, naming, frontmatter, dangling refs, reference-pattern). --prune reads every skill's description and body, then merges skills that duplicate, share a bounded purpose, or share tooling into one consolidated folder, archiving the dropped duplicates. Use when checking a skill or pack against the lint standard, or when consolidating duplicate or overlapping skills.
user-invocable: true
when-to-use: Use when the user wants to check or fix a skill against the lint standard (structure, frontmatter, naming, dangling refs, reference-pattern), or to read all skill descriptions and merge skills that duplicate, share a bounded purpose, or share tooling into one consolidated folder. --prune also runs scheduled headless evolution passes over a skill tree.
argument-hint: "<skills path> [--audit | --prune] [--dry-run | --headless]"
---

# Skill Library

You audit and prune agent skill directories (a collection of `SKILL.md` folders). Two modes own two distinct jobs; pick one per invocation.

**Purpose of this skill:** keep the skill tree at the shared lint standard and collapse overlap. `--audit` makes a target skill (or pack) pass `aa skills lint` and the pre-publish checklist, fixing structure, naming, frontmatter, and dangling references. `--prune` reads every skill's description and body, then merges skills that duplicate, share a bounded purpose, or share tooling into one consolidated folder, archiving the dropped duplicates. Authoring and in-place repair belong to `skill-design`, not here.

## Global Rules

Rules that apply to every step. Reference files cite these; they never restate them.

- **Mode scope**: `--audit` works on a single skill or a pack and makes it conform to the lint standard; `--prune` works on a category or the whole tree and collapses overlap. Each mode routes to its own reference; they do not share state.
- **Audit standard**: `aa skills lint` is the mechanical gate; `references/audit.md` holds the key table, the validator rule catalog, the reference-pattern decision, and the pre-publish checklist. `--audit` applies that standard to the target and fixes every flagged issue.
- **Prune standard**: two skills covering the same job become one folder with one `SKILL.md`; skills that share a domain but differ per scenario stay one folder with one `SKILL.md` plus a `references/` subfolder, one file per scenario, one level deep. Genuinely different jobs stay separate; note why in the report.
- **Prune phase order**: Phase 1 (remove true duplicates) always precedes Phase 2 (consolidate variants). Merging skills that are already true duplicates is wasted effort.
- **Provisioned copies**: same-folder-name mirrors under `.agents/skills/` or a harness home are provisioned artifacts — keep the repo source, flag the copy for re-provisioning, never edit the copy.
- **Byte-identical or near-identical bodies**: merge into one; keep the more complete body, drop the rest.
- **Same `name:` in two folders**: one is stale; keep the more complete, delete the other.
- **Validation rules** (enforced when auditing, pruning, and consolidating skills): unique-skill-name — Each skill name is used by one folder only; unique-description — No two skills share one description; category-description-present — Every category has a DESCRIPTION.md; category-description-nonempty — Category DESCRIPTION.md describes the category; category-nonempty — Every category holds at least one skill; category-depth — No nesting deeper than <category>/<skill>/.
- **Rollback**: the snapshot (or `HEAD` SHA when the tree was dirty) is the undo path; `git reset --hard <sha>` restores both the skill and unrelated state. Record the snapshot SHA in the commit message and final report. A headless run that cannot commit falls back to `--dry-run` and reports instead of applying.
- **Safety model**: `--dry-run` generates the report and stops before any snapshot or execute. `--headless` generates the same report and continues into the snapshot and execute steps, skipping the interactive approval gate. Read-only steps run immediately in either mode. Destructive actions go to `_archive/` first; permanent delete only with explicit `--hard-delete`.
- **Parallel agents committing in the same tree**: this repo is worked on by multiple agents (GrokBuild via Orca, Hermes). A concurrent commit can sweep your staged changes into someone else's commit and change the HEAD you snapshotted against. After any snapshot and before committing, re-run `git log --oneline -4` and `git status`; re-verify on-disk state before executing; keep your commit scoped to your own task files only — never `git add -A`.
- **Staging discipline**: inside `skills/<category>/`, `git add -A .` stages every tracked file under that subdirectory, not just the change's changes. Use explicit top-level paths (`git add skills/<category>/ skills/CATALOG.md`) and verify the staged set with `git status --short` before committing.

## Routing

| Step | Reference | Goal / Purpose |
| ---- | --------- | -------------- |
| `--audit` | [`references/audit.md`](references/audit.md) | **Goal:** make the target skill(s) pass `aa skills lint` and the pre-publish checklist — fix structure, naming, frontmatter, and dangling refs. |
| `--prune` | [`references/prune/`](references/prune/) | **Goal:** read every skill's description and body; merge skills that duplicate, share a bounded purpose, or share tooling into one consolidated folder; archive dropped duplicates. |
