---
name: skill-lifecycle
description: Performs bulk skill-tree operations — prune, consolidate, merge, archive, and weed (detect duplicate/obsolete skills and archive them). Use when cleaning up, auditing, or merging agent skill directories, pruning skills, consolidating skills, merging duplicate skills, collapsing skill folders, or running a scheduled self-evolution pass over a skill tree.
user-invocable: true
when-to-use: Use when the user wants to prune, consolidate, or merge a skill tree; collapse duplicate or near-duplicate skill folders; audit a skill directory for structural issues; weed duplicate or obsolete skills; archive removed skills into `_archive/`; or run a scheduled headless evolution pass that applies approved changes without an interactive approval gate.
argument-hint: "<skill-dir> [--dry-run | --headless]"
---

# Skill Lifecycle

You prune, consolidate, merge, and archive agent skill directories (a collection of `SKILL.md` folders). Two skills covering the same job collapse into one folder with one `SKILL.md`; skills that share a domain but differ per scenario keep one folder with one `SKILL.md` plus a `references/` subfolder, one file per scenario. `<skill-dir>` is the audit root: it may be a category, a single `CATEGORY/SKILL` folder, or the full skill tree. Weeding duplicate or obsolete skills happens as part of the Phase 1/Phase 2 phases over that root. The two-phase structure mirrors `code-quality/deep-clean`: Phase 1 removes true duplicates, Phase 2 consolidates variants.

**Scope:** skill directories only — `SKILL.md` files, `references/`, `scripts/`, and category `DESCRIPTION.md` files. Never touch non-skill content.

## Global Rules

Rules that apply to every step. Reference files cite these; they never restate them.

- **Phase order**: Phase 1 (remove true duplicates) always precedes Phase 2 (consolidate variants). Merging skills that are already true duplicates is wasted effort.
- **One folder, one SKILL.md**: two skills covering the same job become one folder with one `SKILL.md`; skills that share a domain but differ per scenario stay one folder with one `SKILL.md` plus `references/` subfolder, one file per scenario, one level deep. Genuinely different jobs stay separate; note why in the report.
- **Provisioned copies**: same-folder-name mirrors under `.agents/skills/` or a harness home are provisioned artifacts — keep the repo source, flag the copy for re-provisioning, never edit the copy.
- **Byte-identical or near-identical bodies**: merge into one; keep the more complete body, drop the rest.
- **Same `name:` in two folders**: one is stale; keep the more complete, delete the other.
- **Validation rules** (enforced when pruning, merging, and consolidating skills): unique-skill-name — Each skill name is used by one folder only; unique-description — No two skills share one description; category-description-present — Every category has a DESCRIPTION.md; category-description-nonempty — Category DESCRIPTION.md describes the category; category-nonempty — Every category holds at least one skill; category-depth — No nesting deeper than <category>/<skill>/.
- **Rollback**: the snapshot (or `HEAD` SHA when the tree was dirty) is the undo path; `git reset --hard <sha>` restores both the skill and unrelated state. Record the snapshot SHA in the commit message and final report. A headless run that cannot commit falls back to `--dry-run` and reports instead of applying.
- **Scope**: skill directories only. A scoped multi-skill merge (the user names two or more specific folders) skips the full-tree inventory and treats exactly the named skills as the audit set; do not let the default audit root expand the scope beyond the named skills.
- **Safety model**: `--dry-run` generates the prune report (Step 4) and stops before any snapshot or execute. `--headless` generates the same report and continues into the snapshot and execute steps, skipping the interactive approval gate. Read-only steps run immediately in either mode. Destructive actions go to `_archive/` first; permanent delete only with explicit `--hard-delete`.
- **Parallel agents committing in the same tree**: this repo is worked on by multiple agents (GrokBuild via Orca, Hermes). A concurrent commit can sweep your staged changes into someone else's commit and change the HEAD you snapshotted against. After any snapshot and before committing, re-run `git log --oneline -4` and `git status`; re-verify on-disk state before executing; keep your commit scoped to your own task files only — never `git add -A`.
- **Staging discipline**: inside `skills/<category>/`, `git add -A .` stages every tracked file under that subdirectory, not just the prune's changes. Use explicit top-level paths (`git add skills/<category>/ skills/CATALOG.md`) and verify the staged set with `git status --short` before committing.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Step 0 | [`references/step-0-confirm-root.md`](references/step-0-confirm-root.md) | Confirm the audit root; reject a file path or an empty tree. |
| Step 1 | [`references/step-1-inventory.md`](references/step-1-inventory.md) | List every skill folder; read each `SKILL.md` frontmatter and body. |
| Step 2 | [`references/step-2-group.md`](references/step-2-group.md) | Cluster by semantic scope; verify against body content. |
| Step 3 | [`references/step-3-classify.md`](references/step-3-classify.md) | Classify each cluster: duplicate, variant, or separate jobs. |
| Step 4 | [`references/step-4-dry-run.md`](references/step-4-dry-run.md) | Generate the planned prune report; `--dry-run` stops here, `--headless` proceeds straight to Step 5. |
| Step 5 | [`references/step-5-snapshot.md`](references/step-5-snapshot.md) | `git add -A && git commit` or `git stash`; record the rollback target. |
| Step 6 | [`references/step-6-execute.md`](references/step-6-execute.md) | Execute the merge: name survival, frontmatter union, body merge, conflict resolution, scripts, empty-category cleanup, DESCRIPTION.md. |
| Step 7 | [`references/step-7-verify-report.md`](references/step-7-verify-report.md) | Verify every `SKILL.md` parses and links resolve; on failure trigger rollback; output the final report. |
