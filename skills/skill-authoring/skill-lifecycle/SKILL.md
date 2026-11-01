---
name: skill-lifecycle
description: Prunes and consolidates SKILL.md collections — deduplicates overlapping skills into one folder with one SKILL.md, or keeps one folder with a references/ subfolder for complex variants. Use when cleaning up, auditing, or merging agent skill directories (e.g., /skill-lifecycle, or a merge of one skill into another such as merging create-workflow into grok-build), pruning skills, consolidating skills, merging duplicate skills, auditing a skill directory, collapsing skill folders, or running a scheduled self-evolution pass over a skill tree.
when-to-use: Use when cleaning up, auditing, or merging agent skill directories; pruning skills; consolidating skills; merging one skill into another (for example, a merge of create-workflow into grok-build); auditing a skill directory; collapsing skill folders; or running a scheduled (headless) evolution pass that applies approved changes without an interactive approval gate.
argument-hint: "[<skill-dir>] [--dry-run | --auto | --evolution]"
metadata:
  tags:
    - skill
    - pruning
    - deduplication
    - consolidation
    - skill-cleanup
    - agent-skills
---

# Skill Lifecycle

You prune and consolidate agent skill directories (a collection of `SKILL.md` folders). Two skills covering the same job collapse into one folder with one `SKILL.md`; skills that share a domain but differ per scenario keep one folder with one `SKILL.md` plus a `references/` subfolder, one file per scenario. Modeled on `code-quality/deep-clean` (two-phase: remove duplicates, then consolidate variants).

**Scope:** skill directories only — `SKILL.md` files, `references/`, `scripts/`, and category `DESCRIPTION.md` files. Never touch non-skill content.

## Execution Flow

1. **Confirm the audit root**: default `/home/raka/agents-arwaky/skills`, a specific category, or the user's path. Reject a path that resolves to a file, and stop if the directory holds no `SKILL.md` subfolders.
2. **Inventory & classify**: list every skill folder, read each `SKILL.md`, cluster by semantic scope, and classify each cluster as duplicate, variant, or separate jobs (Phase 1 removes true duplicates; Phase 2 consolidates variants — never skip Phase 1).
3. **Dry-run & approval**: generate the planned prune report and present it; wait for confirmation. `--auto` and `--evolution` skip this gate and go straight to the snapshot.
4. **Snapshot**: `git add -A && git commit` (or `git stash` if the tree holds unrelated work — record the `HEAD` SHA and stage only the skill-tree paths you touch).
5. **Execute**: merge per the Phase 2 table; update category `DESCRIPTION.md` and `CATALOG.md`.
6. **Verify & rollback**: every remaining `SKILL.md` parses, all reference links resolve, no two skills share a `name:`, `aa skills validate` is clean. On failure, trigger the Rollback Protocol.
7. **Report**: output the executed `skill-lifecycle report` with the rollback target SHA.

## Global Rules (SSOT)

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
