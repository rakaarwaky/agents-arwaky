---
name: skill-lifecycle
description: Prunes and consolidates SKILL.md collections — deduplicates overlapping skills into one folder with one SKILL.md, or keeps one folder with a references/ subfolder for complex variants. Use when cleaning up, auditing, or merging agent skill directories (e.g., /skill-lifecycle, or a merge of one skill into another such as merging create-workflow into grok-build), pruning skills, consolidating skills, merging duplicate skills, collapsing skill folders, or running a scheduled self-evolution pass over a skill tree.
user-invocable: true
when-to-use: Use when the user wants to prune, consolidate, or merge a skill tree; collapse duplicate or near-duplicate skill folders; audit a skill directory for structural issues; or run a scheduled headless evolution pass that applies approved changes without an interactive approval gate.
argument-hint: "[<skill-dir>] [--dry-run | --auto | --evolution]"
---

# Skill Lifecycle

You prune and consolidate agent skill directories (a collection of `SKILL.md` folders). Two skills covering the same job collapse into one folder with one `SKILL.md`; skills that share a domain but differ per scenario keep one folder with one `SKILL.md` plus a `references/` subfolder, one file per scenario. The two-phase structure mirrors `code-quality/deep-clean`: Phase 1 removes true duplicates, Phase 2 consolidates variants.

**Scope:** skill directories only — `SKILL.md` files, `references/`, `scripts/`, and category `DESCRIPTION.md` files. Never touch non-skill content.

## Invoke Routing

- `--dry-run` → workflow-steps.md — the full per-step checklist from confirm root to report.
- `--auto` / `--evolution` → workflow-steps.md — skip the approval gate and go straight to the snapshot.
- `--merge` → merge-rules.md — name survival, frontmatter union, body merge, conflict resolution.
- `--rollback` → rollback-protocol.md — hard failure, soft failure, and mid-run abort handling.

## Global Rules

Rules that apply to every step. Reference files cite these; they never restate them.

- **Phase order**: Phase 1 (remove true duplicates) always precedes Phase 2 (consolidate variants). Merging skills that are already true duplicates is wasted effort.
- **One folder, one SKILL.md**: two skills covering the same job become one folder with one `SKILL.md`; skills that share a domain but differ per scenario stay one folder with one `SKILL.md` plus `references/` subfolder, one file per scenario, one level deep. Genuinely different jobs stay separate; note why in the report.
- **Provisioned copies**: same-folder-name mirrors under `.agents/skills/` or a harness home are provisioned artifacts — keep the repo source, flag the copy for re-provisioning, never edit the copy.
- **Byte-identical or near-identical bodies**: merge into one; keep the more complete body, drop the rest.
- **Same `name:` in two folders**: one is stale; keep the more complete, delete the other.
- **Validation rules** (enforced by `aa skills validate` when pruning, merging, and consolidating skills): unique-skill-name — Each skill name is used by one folder only; unique-description — No two skills share one description; category-description-present — Every category has a DESCRIPTION.md; category-description-nonempty — Category DESCRIPTION.md describes the category; category-nonempty — Every category holds at least one skill; category-depth — No nesting deeper than <category>/<skill>/.
- **Rollback**: the snapshot (or `HEAD` SHA when the tree was dirty) is the undo path; `git reset --hard <sha>` restores both the skill and unrelated state. Record the snapshot SHA in the commit message and final report. `--evolution` (headless) runs that cannot commit fall back to `--dry-run` and report instead of applying.
- **Scope**: skill directories only. A scoped multi-skill merge (the user names two or more specific folders) skips the full-tree inventory and treats exactly the named skills as the audit set; do not let the default audit root expand the scope beyond the named skills.

## Run Steps

| Mode | Reference | Purpose |
| ---- | --------- | ------- |
| Step details (1–10) | [`references/workflow-steps.md`](references/workflow-steps.md) | The full per-step checklist: confirm root, inventory, group, classify, dry-run & approval, snapshot, execute, update, verify, report. |
| Merge rules | [`references/merge-rules.md`](references/merge-rules.md) | Name survival, frontmatter union, body merge, conflict resolution, scripts, empty-category cleanup, DESCRIPTION.md handling. |
| Report format | [`references/report-format.md`](references/report-format.md) | The final executed report shape: MERGED / KEPT SEPARATE / DELETED / ROLLBACK TARGET / VERIFY. |
| Rollback protocol | [`references/rollback-protocol.md`](references/rollback-protocol.md) | Hard failure, soft failure, and mid-run abort handling. |
| Common mistakes | [`references/common-mistakes.md`](references/common-mistakes.md) | The failure list to re-check before declaring the prune done. |
| Safety model | [`references/safety.md`](references/safety.md) | What this skill may and may not touch. |
