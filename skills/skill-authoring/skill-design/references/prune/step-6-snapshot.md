# Step 6: Snapshot

Create the rollback point before executing any merge.

**Goal:** commit (or stash) the pre-prune state and record the rollback target.

## Commands

Stage the skill-tree paths you touch and commit (`git commit -m "snapshot: before skill-design prune"`). If the tree is dirty for other reasons, `git stash` instead; record the `HEAD` SHA as the rollback target (Global Rules: Rollback).

When the tree holds unrelated in-progress changes, stage only the skill-tree paths you touch — never `git add -A` into the same commit as unrelated work. Use explicit paths (`git add skills/<category>/ skills/catalog.json`) and verify the staged set with `git status --short`. A path typo or a sibling subagent committing concurrent work in the same checkout silently pulls unrelated deletions into the commit; unstage anything that is not part of the prune.

## Completion

- The snapshot commit (or stash ref) exists and its SHA is recorded.
- `git status --short` shows only skill-tree paths staged, no unrelated work.
- The rollback target is available to Step 8.
